import asyncio
import websockets
import sys
import aioconsole
import json

session_id = sys.argv[1]


async def receive_messages(websocket):
  async for message in websocket:
      print(message)


async def send_guesses(websocket):
  while True:
      guess = await aioconsole.ainput('Guess: ')

      message = {
        "action": "guess",
        "guess": guess
      }
      await websocket.send( json.dumps(message) )




async def hello():
    uri = f"ws://localhost:6789/{session_id}"
    async with websockets.connect(uri) as websocket:
      await asyncio.wait([
        asyncio.create_task(receive_messages(websocket)),
        asyncio.create_task(send_guesses(websocket))
      ])
       
        

asyncio.get_event_loop().run_until_complete(hello())
