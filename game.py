#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets
from random import randint
from datetime import datetime

import enum

import db

PUZZLES = []
for c in db.Cluster.select():
    PUZZLES.append((c.cluster, c.words))
N_PUZZLES = len(PUZZLES)


logging.basicConfig()


SESSIONS = {}


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
        self.puzzle_id = None
        self.words = []


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
            player_ids = list(self.players.keys())
            game_id = list(SESSIONS.keys())[0]
            self.db_game = db.Game.create(game_id=game_id, user1=player_ids[0], user2=player_ids[1], guess='')
            # # Send first puzzle
            self.puzzle_id, self.words = PUZZLES[randint(0, N_PUZZLES)]
            await self._send_message_to_all_players({"type": "state", "value": f"What's the concept for: {self.words}"})
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
            await self._send_message_to_all_players(f"Matched with: {guess}")
            self.db_game.guess = guess
            self.db_game.save()
            self.puzzle_id, self.words = PUZZLES[randint(0, N_PUZZLES)]
            await self._send_message_to_all_players({"type": "state", "value": f"What's the concept for: {self.words}"})
            self.start_time = datetime.now()


    def state_event(self):
        return json.dumps({"type": "state", "value": f"What's the concept for: {self.words}"})



async def game(websocket, path):
    session_id = path

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
