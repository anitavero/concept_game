#!/usr/bin/env python
import os
import asyncio
import json
import logging
import websockets
from random import randrange
from datetime import datetime, timedelta
from time import sleep
from collections import OrderedDict
import uuid

from concept_game_backend import db, read_tables


PUZZLES = []
for c in db.Cluster.select():
    PUZZLES.append((c.cluster, c.words))
N_PUZZLES = len(PUZZLES)


logging.basicConfig()


class GamePlayer():
    def __init__(self, websocket):
        self.websocket = websocket
        self.guesses = set()


AUTO = 'AUTO'
class AutoPlayer():

    def __init__(self):
        self.guesses = set()
# TODO: stop generation if player left
    async def generate_guesses(self, cluster_id, db_game):
        guesses = read_tables.select_answers_by_cluster_id(cluster_id)
        print('Generate guesses', len(guesses))
        for user, guess, etime in guesses:
            elapsed_time = timedelta(seconds=etime.second, microseconds=etime.microsecond).total_seconds()
            sleep(elapsed_time)
            self.guesses.add(guess)
            a = db.Answer.create(game=db_game, cluster_id=cluster_id, user=AUTO, word=guess,
                                 e_time=elapsed_time)
            print('AUTO guess:', self.guesses, etime)


class SessionHandler():

    def __init__(self):
        self.sessions = OrderedDict()

    def real_player_ids_of_last_sess(self):
        return [pid for pid in self.last_session_values().player_ids if pid != AUTO]

    async def remove_auto_if_exists(self):
        await self.last_session_values().unregister_autoplayer()

    def last_session_id(self):
        return list(self.sessions.keys())[-1]

    def last_session_values(self):
        return list(self.sessions.values())[-1]


SH = SessionHandler()


class GameSession():
    def __init__(self):
        self.players = {}
        self.autoplayer = None
        self.db_game = None
        self.start_time = None
        self.puzzle_id = ''
        self.words = []
        self.score = 0
        self.game_id = ''
        self.player_ids = []


    def get_other_player_id(self, player_id):
        if self.autoplayer:
            if player_id == AUTO:
                return 1
            else:
                return AUTO
        elif player_id == 1:
            return 2
        elif player_id == 2:
            return 1
        else:
            raise Exception(f"Unknown player_id {player_id}")

    async def send_message_to_all_players(self, message):
        message_json = json.dumps(message)
        await asyncio.wait([
            asyncio.create_task(p.websocket.send(message_json)) for pid, p in self.players.items() if pid != AUTO])

    async def send_message_to_client(self, message, websocket):
        message_json = json.dumps(message)
        await asyncio.wait([
            asyncio.create_task(websocket.send(message_json))])

    async def send_message_to_other_player(self, message, player_id):
        other_id = self.get_other_player_id(player_id)
        if other_id in self.players and other_id != AUTO:
            websocket = self.players[other_id].websocket
            await self.send_message_to_client(message, websocket)

    async def register_player(self, websocket) -> int:
        player = GamePlayer(websocket)

        # TODO: player_id should be IP address or sth
        if 1 not in self.players:
            player_id = 1
        elif 2 not in self.players:
            player_id = 2
        else:
            raise Exception("Full but not detected.")

        self.players[player_id] = player

        if len(self.players) == 2 or self.autoplayer:
            self.player_ids += list(self.players.keys())
            self.player_ids = list(set(self.player_ids))
            if self.autoplayer:
                self.players[AUTO] = self.autoplayer
            self.game_id = SH.last_session_id()
            await self.new_puzzle()

        return player_id

    async def unregister_player(self, player_id):
        await self.send_message_to_other_player({"type": "other_player_abandoned_game"}, player_id)
        del self.players[player_id]
        self.player_ids.remove(player_id)
        if len(self.players) > 0:
            print("Add AutoPlayer")
            self.autoplayer = AutoPlayer()
            self.player_ids.append(AUTO)
            self.players[AUTO] = self.autoplayer
            await self.autoplayer.generate_guesses(self.puzzle_id, self.db_game)
            self.score = 0

    async def unregister_autoplayer(self):
        if AUTO in self.player_ids:
            del self.players[AUTO]
            self.player_ids.remove(AUTO)
            self.autoplayer = None
            # Send message about human player
            self.score = 0
            await self.send_message_to_all_players({"type": "human_player"})

    def is_empty(self):
        return len(self.players)==0

    async def new_puzzle(self):
        """Send puzzle to users"""
        self.puzzle_id, self.words = PUZZLES[randrange(0, N_PUZZLES)]
        await self.send_message_to_all_players({"type": "words", "words": self.words})
        self.start_time = datetime.now()
        self.db_game = db.Game.create(game_id=self.game_id, start_time=self.start_time, cluster_id=self.puzzle_id,
                                      user1=self.player_ids[0], user2=self.player_ids[1], guess='')
        if self.autoplayer:
            await self.autoplayer.generate_guesses(self.puzzle_id, self.db_game)

    async def add_guess(self, player_id, guess, timeout):
        if timeout:
            await self.send_message_to_all_players({"type": "timeout"})
            guess = 'TIMEOUT'

        time = datetime.now()
        guess = guess.lower().strip()
        elapsed_time = time - self.start_time
        self.players[player_id].guesses.add( guess )

        print(self.puzzle_id, guess, elapsed_time)


        a = db.Answer.create(game=self.db_game, cluster_id=self.puzzle_id, user=player_id, word=guess, e_time=elapsed_time)

        other_player_id = self.get_other_player_id(player_id)

        match = False
        if guess in self.players[other_player_id].guesses:
            match = True
            if guess != 'pass':
                self.score += 1
            await self.send_message_to_all_players({"type": "score", "score": self.score, "match": guess})
            self.db_game.guess = guess
            self.db_game.save()

        if match or timeout:
            # New puzzle
            for pid in self.players.keys():
                self.players[pid].guesses = set()  # Clear guesses for new puzzle
            await self.new_puzzle()


async def serve_queue(websocket):
    print('QUEUE')
    try:
        async for message in websocket:
            print('Client message', message)
            data = json.loads(message)
            if data["action"] == "play":
                # Create unique id for each GameSession.
                if len(SH.sessions) == 0:
                    session_id = str(uuid.uuid1())
                elif len(SH.real_player_ids_of_last_sess()) == 1:
                    print("Replace AutoPlayer.")
                    session_id = SH.last_session_id()
                    await SH.remove_auto_if_exists()
                else:
                    session_id = str(uuid.uuid1())

                if session_id not in SH.sessions:
                    print("creating new session", session_id)
                    SH.sessions[session_id] = GameSession()

                if len(SH.real_player_ids_of_last_sess()) == 0:
                    print("Add AutoPlayer")
                    SH.sessions[session_id].autoplayer = AutoPlayer()
                    SH.sessions[session_id].player_ids.append(AUTO)

                game_session = SH.sessions[session_id]
                print('Queue sends session_id:', session_id)
                await game_session.send_message_to_client({"type": "session", "session_id": session_id},
                                                          websocket)
            else:
                logging.error(f"unsupported event: {data}")
    except websockets.exceptions.ConnectionClosedError as err:
        print('Queue server error:', str(err))


async def serve_game_session(websocket, session_id):
    print('GAME')
    game_session = SH.sessions[session_id]
    player_id = await game_session.register_player(websocket)
    try:
        async for message in websocket:
            print("Player", player_id, message)
            data = json.loads(message)
            if data["action"] == "guess":
                await game_session.add_guess(player_id, data["guess"], False)
            elif data["action"] == "timeout":
                await game_session.add_guess(player_id, '', True)
            else:
                logging.error(f"unsupported event: {data}")
    except websockets.exceptions.ConnectionClosedError as err:
        print('Game server error:', str(err), 'Player', player_id)    # client went away
    finally:
        print('Game finally', list(SH.sessions.keys()), "Player", player_id)
        await game_session.unregister_player(player_id)
        if session_id in SH.sessions.keys() and SH.sessions[session_id].player_ids == []:
            del SH.sessions[session_id]


async def server(websocket, path):
    if path == "/queue":
        await serve_queue(websocket)

    elif path.startswith("/session/"):
        session_id = os.path.split(path)[1]
        print("Client game", session_id)
        await serve_game_session(websocket, session_id)


if __name__ == "__main__":
    start_server = websockets.serve(server, "", 6789)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
