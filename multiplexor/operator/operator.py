
import asyncio
import websockets

from .protocol import *

class Operator:
	def __init__(self):
		self.server_url = None
		self.ws = None
		
		self.server_cmd_q = asyncio.Queue()
		
	async def handle_server_in(self):
		while True:
			data = await self.ws.recv()
			print('RPLY in!')
			rply = OperatorCmdParser.from_json(data)
			print(rply.to_dict())
		
	async def handle_server_out(self):
		while True:
			cmd = await self.server_cmd_q.get()
			await self.ws.send(json.dumps(cmd.to_dict()))
			print('CMD sent!')
		
	async def connect(self):
		print('Connecting!')
		while True:
			self.ws = await websockets.connect(self.server_url)
			asyncio.ensure_future(self.handle_server_in())
			asyncio.ensure_future(self.handle_server_out())
			
			await self.ws.wait_closed()
			asyncio.sleep(10)
			print('Reconnecting!')
			
			
	
	async def send_test_data(self):
		self.server_url = 'ws://127.0.0.1:9999'
		asyncio.ensure_future(self.connect())
		#await asyncio.sleep(3)
		print('Sending command')
		cmd = OperatorListAgentsCmd()
		await self.server_cmd_q.put(cmd)
		await asyncio.sleep(10)