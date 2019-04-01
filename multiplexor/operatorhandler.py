import websockets
import asyncio

from .operator.protocol import *

class OperatorHandler:
	def __init__(self, listen_ip, listen_port, sslctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.sslctx = sslctx
		
		self.multiplexor_cmd_in = asyncio.Queue()
		self.multiplexor_cmd_out = asyncio.Queue()
		
		self.transport_closed = asyncio.Event()
		
	async def handle_incoming_cmds(self, websocket):
		while not self.transport_closed.is_set():
			try:
				data = await websocket.recv()
				cmd = OperatorCmdParser.from_json(data)
				await self.multiplexor_cmd_in.put(cmd)
			except Exception as e:
				print(e)
			
	async def handle_outgoing_cmds(self, websocket):
		while not self.transport_closed.is_set():
			try:
				cmd = await self.multiplexor_cmd_out.get()
				await websocket.send(json.dumps(cmd.to_dict()))
			except Exception as e:
				print(e)

	async def handle_operator(self, websocket, path):
		print('Operator connected!')
		
		asyncio.ensure_future(self.handle_incoming_cmds(websocket))
		asyncio.ensure_future(self.handle_outgoing_cmds(websocket))
		await websocket.wait_closed()
		self.transport_closed.set()
		print('Operator disconnected!')
		
	
	async def run(self):
		try:
			server = await websockets.serve(self.handle_operator, self.listen_ip, self.listen_port, ssl=self.sslctx)
			await server.wait_closed()
		except Exception as e:
			print(e)