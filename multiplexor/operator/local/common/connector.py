import asyncio
import websockets
import json

from multiplexor.operator.protocol import OperatorCmdParser
from multiplexor.logger.logger import mpexception, Logger



class MultiplexorOperatorConnector:
	def __init__(self, server_url, logQ, ssl_ctx = None, reconnect_interval = 5, reconnect_tries = None):
		self.logger = Logger("Connector", logQ)
		self.server_url = server_url
		self.ssl_ctx = ssl_ctx
		self.reconnect_interval = reconnect_interval
		self.reconnect_tries = reconnect_tries

		self.cmd_out_q = asyncio.Queue()
		self.cmd_in_q = asyncio.Queue()
		self.server_connected = asyncio.Event() #this variable is used to signal status towards the modules
		self.in_task = None
		self.out_task = None
		self.current_ws = None

	@mpexception
	async def cmd_in(self, ws):
		while ws and ws.open:
			data = await ws.recv()
			cmd = OperatorCmdParser.from_json(data)
			await self.cmd_in_q.put(cmd)

	@mpexception
	async def cmd_out(self, ws):
		while ws and ws.open:
			rply = await self.cmd_out_q.get()
			await ws.send(json.dumps(rply.to_dict()))

	@mpexception
	async def terminate(self):
		if self.in_task:
			self.in_task.cancel()
		if self.out_task:
			self.out_task.cancel()
		if self.current_ws:
			try:
				#this is ugly, I know BUT official way takes FOREVER to close...
				self.current_ws.writer._transport.abort()
				#await self.current_ws.close()
			except:
				pass
			
		self.in_task = None
		self.out_task = None
		self.current_ws = None


	async def run(self):
		while True:
			if self.reconnect_tries is not None:
				self.reconnect_tries -= 1
				if self.reconnect_tries < 0:
					return
			await self.logger.debug('Connecting to server')
			try:
				ws = await websockets.connect(self.server_url)
				self.current_ws = ws
				self.in_task = asyncio.create_task(self.cmd_in(ws))
				self.out_task = asyncio.create_task(self.cmd_out(ws))

				self.server_connected.set()
				await ws.wait_closed()
				self.server_connected.clear()
				self.in_task.cancel()
				self.out_task.cancel()
				self.in_task = None
				self.out_task = None
				self.current_ws = None

			except asyncio.CancelledError:
				return
			except Exception as e:
				await self.logger.exception('Error connecting to server!')
			else:
				await self.logger.debug('Connection lost to server! Reconnecting in %s seconds' % self.reconnect_interval)
			await asyncio.sleep(self.reconnect_interval)