import asyncio
import websockets
import json

from multiplexor.operator.protocol import OperatorCmdParser
from multiplexor.logger.logger import mpexception, Logger


class MultiplexorOperatorListener:
	"""
	Listens for incoming traffic from the multiplexor server via the JS client
	be careful, this class will handle only one incoming server traffic!
	"""
	def __init__(self, listen_ip, listen_port, logQ, ssl_ctx = None, reconnect_interval = 5):
		self.logger = Logger("Connector", logQ)
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.reconnect_interval = reconnect_interval

		self.cmd_out_q = asyncio.Queue()
		self.cmd_in_q = asyncio.Queue()
		self.server_connected = asyncio.Event() #this event is for other objects, do not remove!
		self.in_task = None
		self.out_task = None

	@mpexception
	async def cmd_in(self, ws):
		while ws.open:
			data = await ws.recv()
			rply = OperatorCmdParser.from_json(data)
			await self.cmd_in_q.put(rply)

	@mpexception
	async def cmd_out(self, ws):
		while ws.open:
			cmd = await self.cmd_out_q.get()
			await ws.send(json.dumps(cmd.to_dict()))

	@mpexception
	async def handle_server(self, ws, path):
		"""
		be careful, this class will handle only one incoming server traffic!
		"""
		if self.server_connected.is_set():
			await self.logger.error('Another proxy connection was initiated, but one is still active')
			return
		
		await self.logger.info('Got connection!')
		
		
		self.in_task = asyncio.create_task(self.cmd_in(ws))
		self.out_task = asyncio.create_task(self.cmd_out(ws))

		self.server_connected.set()
		
		await ws.wait_closed()
		await self.logger.info('Connection to server lost! Reconnect with your proxy again!')
		self.server_connected.clear()
		self.in_task.cancel()
		self.out_task.cancel()
		self.in_task = None
		self.out_task = None
		

	@mpexception
	async def run(self):
		while True:
			await self.logger.info('Waiting for incoming connection!')
			server = await websockets.serve(self.handle_server, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
			await server.wait_closed()
			await asyncio.sleep(self.reconnect_interval)
			