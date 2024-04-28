from websocket import create_connection
import json

url = "wss://v7inbunl4h.execute-api.us-east-1.amazonaws.com/dev"

ws = create_connection(url)
print("Connected")
ws.send(json.dumps({"action": "hello", "message": "Hello, World"}))
result = ws.recv()
print("Received '%s'" % result)
ws.close()
