#!/usr/bin/env python

# WS server example that synchronizes state across clients
import os
import asyncio
import json
import logging
import websockets
from random import randrange
from datetime import datetime
from collections import OrderedDict
import uuid

import enum

from concept_game_backend import db

PUZZLES = []
for c in db.Cluster.select():
    PUZZLES.append((c.cluster, c.words))
N_PUZZLES = len(PUZZLES)


logging.basicConfig()


SESSIONS = OrderedDict()


class GameSessionState(enum.Enum):
    WAITING_FOR_PLAYERS = 1
    GUESSING = 2
    WON = 3
    GAME_ABANDONED = 4


class GamePlayer():
    def __init__(self, websocket):
        self.websocket = websocket
        self.guesses = set()


def get_other_player_id(player_id):
    if player_id == 1:
        return 2
    elif player_id == 2:
        return 1
    else:
        raise Exception(f"Unknown player_id {player_id}")


class GameSession():
    def __init__(self):
        self.players = {}
        self.session_state = GameSessionState.WAITING_FOR_PLAYERS
        self.db_game = None
        self.start_time = None
        self.puzzle_id = ''
        self.words = []
        self.score = 0
        self.game_id = ''
        self.player_ids = []


    async def send_message_to_all_players(self, message):
        message_json = json.dumps(message)
        await asyncio.wait([
            asyncio.create_task(p.websocket.send(message_json)) for p in self.players.values()])

    async def send_message_to_client(self, message, websocket):
        message_json = json.dumps(message)
        await asyncio.wait([
            asyncio.create_task(websocket.send(message_json))])


    async def register_player(self, websocket) -> int:
        if self.session_state!=GameSessionState.WAITING_FOR_PLAYERS:
            raise Exception("This game is already full.")

        player = GamePlayer(websocket)

        # TODO: player_id should be IP address or sth
        if 1 not in self.players:
            player_id = 1
        elif 2 not in self.players:
            player_id = 2
        else:
            raise Exception("Full but not detected.")

        self.players[player_id] = player

        if len(self.players)==2:
            self.session_state=GameSessionState.GUESSING
            self.player_ids = list(self.players.keys())
            self.game_id = list(SESSIONS.keys())[-1]
            await self.new_puzzle()

        return len(self.players)

    async def unregister_player(self, player_id):
        del self.players[player_id]

        if self.session_state==GameSessionState.GUESSING:
            self.session_state = GameSessionState.GAME_ABANDONED
            await self.send_message_to_all_players({"type": "other_player_abandoned_game"})

    def is_empty(self):
        return len(self.players)==0

    async def new_puzzle(self):
        """Send puzzle to users"""
        self.puzzle_id, self.words = PUZZLES[randrange(0, N_PUZZLES)]
        await self.send_message_to_all_players({"type": "words", "words": self.words})
        self.start_time = datetime.now()
        self.db_game = db.Game.create(game_id=self.game_id, start_time=self.start_time, cluster_id=self.puzzle_id,
                                      user1=self.player_ids[0], user2=self.player_ids[1], guess='')

    async def add_guess(self, player_id, guess):
        time = datetime.now()
        guess = guess.lower().strip()
        elapsed_time = time - self.start_time
        self.players[player_id].guesses.add( guess )

        print(self.puzzle_id, guess, elapsed_time)


        a = db.Answer.create(game=self.db_game, cluster_id=self.puzzle_id, user=player_id, word=guess, e_time=elapsed_time)

        other_player_id = get_other_player_id(player_id)

        if guess in self.players[other_player_id].guesses:
            self.session_state = GameSessionState.WON
            if guess != 'pass':
                self.score += 1
            await self.send_message_to_all_players({"type": "score", "score": self.score})
            self.db_game.guess = guess
            self.db_game.save()

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
                if len(SESSIONS) == 0:
                    session_id = str(uuid.uuid1())
                elif len(list(SESSIONS.values())[-1].players) < 2:
                    session_id = list(SESSIONS.keys())[-1]
                else:
                    session_id = str(uuid.uuid1())

                if session_id not in SESSIONS:
                    print("creating new session", session_id)
                    SESSIONS[session_id] = GameSession()

                game_session = SESSIONS[session_id]
                await game_session.send_message_to_client({"type": "session", "session_id": session_id},
                                                          websocket)
            else:
                logging.error("unsupported event: {}", data)
    except websockets.exceptions.ConnectionClosedError:
        pass # client went away whatever


async def serve_game_session(websocket, session_id):
    print('GAME')
    game_session = SESSIONS[session_id]
    player_id = await game_session.register_player(websocket)
    try:
        async for message in websocket:
            print("Player", player_id, message)
            data = json.loads(message)
            if data["action"] == "guess":
                await game_session.add_guess(player_id, data["guess"])
            else:
                logging.error("unsupported event: {}", data)
    except websockets.exceptions.ConnectionClosedError:
        pass    # client went away whatever
    finally:
        await game_session.unregister_player(player_id)
        if game_session.is_empty():
            del SESSIONS[session_id]


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
