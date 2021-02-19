#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets
from random import randint
from datetime import datetime
from collections import OrderedDict
import uuid

import enum

import db

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


    async def _send_message_to_all_players(self, message):
        message_json = json.dumps(message)
        await asyncio.wait([
            asyncio.create_task(p.websocket.send(message_json)) for p in self.players.values()])


    async def register_player(self, websocket) -> int:
        if self.session_state!=GameSessionState.WAITING_FOR_PLAYERS:
            raise Exception("This game is already full.")

        player = GamePlayer(websocket)

        if 1 not in self.players:
            player_id = 1
        elif 2 not in self.players:
            player_id = 2
        else:
            raise Exception("Full but not detected.")


        self.players[player_id] = player

        if len(self.players)==2:
            self.session_state=GameSessionState.GUESSING
            # Add current game to Game table
            self.player_ids = list(self.players.keys())
            self.game_id = list(SESSIONS.keys())[-1]

            await self._send_message_to_all_players({"type": "users", "count": 2})

            # # Send first puzzle
            self.puzzle_id, self.words = PUZZLES[randint(0, N_PUZZLES)]
            self.db_game = db.Game.create(game_id=self.game_id, cluster_id=self.puzzle_id, user1=self.player_ids[0],
                                          user2=self.player_ids[1], guess='')
            await self._send_message_to_all_players({"type": "state", "value": f"{self.words}"})
            self.start_time = datetime.now()

        return len(self.players)

    async def unregister_player(self, player_id):
        del self.players[player_id]

        if self.session_state==GameSessionState.GUESSING:
            self.session_state = GameSessionState.GAME_ABANDONED
            await self._send_message_to_all_players({"type": "other_player_abandoned_game"})

    def is_empty(self):
        return len(self.players)==0


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
            await self._send_message_to_all_players({"type": "match"})
            self.score += 1
            await self._send_message_to_all_players({"type": "score", "score": self.score})
            self.db_game.guess = guess
            self.db_game.save()

            # New puzzle
            for pid in self.players.keys():
                self.players[pid].guesses = set()  # Clear guesses for new puzzle
            self.puzzle_id, self.words = PUZZLES[randint(0, N_PUZZLES)]
            self.db_game = db.Game.create(game_id=self.game_id, cluster_id=self.puzzle_id, user1=self.player_ids[0],
                                          user2=self.player_ids[1], guess='')
            await self._send_message_to_all_players({"type": "state", "value": f"{self.words}"})
            self.start_time = datetime.now()




async def game(websocket, path):

    # Create unique id for each game and increment GameSession ids.
    if len(SESSIONS) == 0:
        session_id = str(uuid.uuid1()) + '_0'
    elif len(list(SESSIONS.values())[-1].players) < 2:
        session_id = list(SESSIONS.keys())[-1]
    else:
        id, seq = list(SESSIONS.keys())[-1].split('_')
        session_id = id + '_' + str(int(seq) + 1)

    if session_id not in SESSIONS:
        SESSIONS[session_id] = GameSession()

    game_session = SESSIONS[session_id]
    player_id = await game_session.register_player( websocket )

    try:
        async for message in websocket:
            print(message)
            data = json.loads(message)
            if data["action"] == "guess":
                await game_session.add_guess(player_id, data["guess"][-2])
            else:
                logging.error("unsupported event: {}", data)
    except websockets.exceptions.ConnectionClosedError:
        pass # client went away whatever
    finally:
        await game_session.unregister_player(player_id)
        if game_session.is_empty():
            del SESSIONS[session_id]


start_server = websockets.serve(game, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
