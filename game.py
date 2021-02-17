#!/usr/bin/env python

# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

import enum

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

            await self._send_message_to_all_players({"type": "start_session"})

        return len(self.players)

    async def unregister_player(self, player_id):
        del self.players[player_id]

        if self.session_state==GameSessionState.GUESSING:
            self.session_state = GameSessionState.GAME_ABANDONED
            await self._send_message_to_all_players({"type": "other_player_abandoned_game"})

    def is_empty(self):
        return len(self.players)==0


    async def add_guess(self, player_id, guess):
        guess = guess.lower().strip()
        self.players[player_id].guesses.add( guess )

        other_player_id = get_other_player_id(player_id)

        if guess in self.players[other_player_id].guesses:
            self.session_state = GameSessionState.WON
            await self._send_message_to_all_players({"type": "match", "which_guess": guess})








async def game(websocket, path):
    session_id = path

    if session_id not in SESSIONS:
        SESSIONS[session_id] = GameSession()

    game_session = SESSIONS[session_id]
    player_id = await game_session.register_player( websocket )

    try:
        async for message in websocket:
            data = json.loads(message)
            if data["action"] == "guess":
                await game_session.add_guess(player_id, data["guess"])
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
