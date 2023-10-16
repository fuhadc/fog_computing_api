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

        # Send messages or data to the server
        while True:
            message = input("Enter a message: ")
            await websocket.send(message)

# Run the publisher client
asyncio.get_event_loop().run_until_complete(main())
