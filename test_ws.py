import asyncio
import websockets

async def test():
    uri = "ws://127.0.0.1:8000/discover/ws/discover?role=React"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            msg = await websocket.recv()
            print(f"Received: {msg}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test())
