import asyncio
import websockets

API_KEY = "DSZdBdP1wP1stFE39lGW0jUQ5uGyzN4A"
SERVER_URI = "ws://localhost:8765"

async def main():
    async with websockets.connect(SERVER_URI) as websocket:
        # Authenticate with the server using API key
        await websocket.send(API_KEY)
        response = await websocket.recv()
        print(response)  # Should be "Authorized: Connection successful"

        # Receive messages or data from the server
        while True:
            message = await websocket.recv()
            print("Received:", message)

# Run the subscriber client
asyncio.get_event_loop().run_until_complete(main())
