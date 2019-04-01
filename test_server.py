import asyncio
import websockets

async def hello(websocket, path):
	data = b'\x00\x00\x00\x07\x00\x01\x00\x00\x00\x01\x00' #+ b'\x00\x00\x00\x07\x01\x01\x00\x00\x00\x01\x00'
	data += b'\x00\x00\x01\x0D\x02\x02\x00\x00\x00\x04\x00\x00\x00\x01\x00\x00\x00\xff' + b'\x0A'*255
	await websocket.send(data[:7])
	await asyncio.sleep(1)
	await websocket.send(data[7:10])
	await asyncio.sleep(1)
	await websocket.send(data[10:])
	name = await websocket.recv()
	print(f"< {name}")

	greeting = f"Hello {name}!"

	await websocket.send(greeting)
	print(f"> {greeting}")

start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()