import asyncio
import websockets
from pymongo import MongoClient
import config

MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(config.MONGO_URI)
db = client.systems
users = db.users

API_KEYS_COLLECTION = "api_keys"

async def handle_connection(websocket, path):
    try:
        # Receive API key from the client
        received_key = await websocket.recv()

        # Validate the received API key
        valid_key = users.find_one({'api_key': received_key})
        if valid_key:
            await websocket.send("Authorized: Connection successful")
            
            while True:
                # Handle other WebSocket logic here
                message = await websocket.recv()
                # Process and respond to messages as needed
        else:
            await websocket.send("Unauthorized: Invalid API key")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")

# Close the MongoDB connection when the WebSocket server is shutting down
def close_mongo_connection():
    client.close()

start_server = websockets.serve(handle_connection, "localhost", 8765)

async def main():
    await start_server

# Start the WebSocket server
try:
    asyncio.get_event_loop().run_until_complete(main())
    asyncio.get_event_loop().run_forever()
except KeyboardInterrupt:
    close_mongo_connection()
