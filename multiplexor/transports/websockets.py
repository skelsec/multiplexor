import asyncio
import websockets
import uuid
from multiplexor.packetizer import Packetizer
from multiplexor.agenthandler import MultiplexorAgentHandler
from multiplexor.logger.logger import *

class WebsocketsTransportServer:
	def __init__(self, listen_ip, listen_port, logging_queue, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.logger = Logger('WebsocketsTransportServer', logQ = logging_queue)
		self.agent_dispatch_queue = None #will be defined by the server!
			
	@mpexception	
	async def handle_packetizer_send(self, agent):
		while not agent.trasnport_terminated_evt.is_set():
			data = await agent.packetizer.packetizer_out.get()
			try:
				await agent.transport.send(data)
			except websockets.exceptions.ConnectionClosed:
				agent.trasnport_terminated_evt.set()
				return
				
	@mpexception	
	async def handle_packetizer_recv(self, agent):
		while not agent.trasnport_terminated_evt.is_set():
			try:
				data = await agent.transport.recv()
			except websockets.exceptions.ConnectionClosed:
				agent.trasnport_terminated_evt.set()
				return
			await agent.packetizer.packetizer_in.put(data)
	
	@mpexception
	async def handle_agent(self, websocket, path):
		print('Agent connected!')
		agent = MultiplexorAgentHandler(self.logger.logQ)
		agent.transport = websocket
		agent.packetizer = Packetizer(self.logger.logQ, agent.trasnport_terminated_evt)
		
		asyncio.ensure_future(agent.packetizer.run())
		asyncio.ensure_future(self.handle_packetizer_send(agent))
		asyncio.ensure_future(self.handle_packetizer_recv(agent))
		await self.agent_dispatch_queue.put(agent)
		
		await agent.transport.wait_closed()
		agent.trasnport_terminated_evt.set()
		print('Agent disconnected!')
		
	@mpexception
	async def run(self):
		try:
			server = await websockets.serve(self.handle_agent, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
			await server.wait_closed()
		except Exception as e:
			print(e)