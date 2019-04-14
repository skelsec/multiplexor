import websockets
import asyncio
import uuid
import json

from multiplexor.operator.protocol import *
from multiplexor.logger.logger import *

class Operator:
	def __init__(self, websocket, operator_id, logQ):
		self.logger = Logger('Operator %s' % operator_id, logQ=logQ)
		self.websocket = websocket
		self.operator_id = operator_id
		self.multiplexor_cmd_in = asyncio.Queue()
		self.multiplexor_cmd_out = asyncio.Queue()
		self.transport_closed = asyncio.Event()

	async def process_log(self, logmsg):
		if not self.transport_closed.is_set():
			try:
				t = OperatorLogEvent()
				t.level = logmsg.level
				t.name = logmsg.name
				t.msg = logmsg.msg
				t.agent_id = logmsg.agent_id

				await self.websocket.send(json.dumps(t.to_dict()))
			except Exception as e:
				await self.logger.error(e)

class OperatorHandler:
	def __init__(self, listen_ip, listen_port, logQ, sslctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.sslctx = sslctx
		self.transport_terminated_evt = asyncio.Event()
		
		self.operator_dispatch_queue = None
		
		self.logger = Logger('OperatorHandler', logQ = logQ)
		
	@mpexception
	async def handle_incoming_cmds(self, operator):
		while not operator.transport_closed.is_set():
			try:
				data = await operator.websocket.recv()
			except websockets.exceptions.ConnectionClosed:
				operator.transport_closed.set()
				return
			cmd = OperatorCmdParser.from_json(data)
			await operator.multiplexor_cmd_in.put(cmd)
	
	@mpexception
	async def handle_outgoing_cmds(self, operator):
		while not operator.transport_closed.is_set():
			try:
				cmd = await operator.multiplexor_cmd_out.get()
				await operator.websocket.send(json.dumps(cmd.to_dict()))
			except Exception as e:
				await self.logger.error(e)
				continue
	@mpexception
	async def handle_operator(self, websocket, path):
		await self.logger.debug('Operator connected!')
		
		operator = Operator(websocket, str(uuid.uuid4()), self.logger.logQ)
		asyncio.ensure_future(self.handle_incoming_cmds(operator))
		asyncio.ensure_future(self.handle_outgoing_cmds(operator))
		await self.operator_dispatch_queue.put(operator)
		await websocket.wait_closed()
		operator.transport_closed.set()
		await self.logger.debug('Operator disconnected!')
		
	@mpexception
	async def run(self):
		try:
			await self.logger.debug('Serving..')
			server = await websockets.serve(self.handle_operator, self.listen_ip, self.listen_port, ssl=self.sslctx)
			await server.wait_closed()
			self.transport_terminated_evt.set()
		except Exception as e:
			print(e)