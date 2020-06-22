import asyncio
import websockets
import uuid
import base64
import urllib.parse
from multiplexor.server.packetizer import Packetizer
from multiplexor.server.agent import MultiplexorAgent
from multiplexor.logger.logger import mpexception, Logger


class HTTP11Transport:
	def __init__(self,reader, writer):
		self.send_q = None
		self.recv_q = None
		self.error = None
		self.reader = reader
		self.writer = writer
		self.incoming_task = None
		self.template = b"""HTTP/1.1 200 OK\r\nConnection: Close\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: %s\r\nDate: Mon, 18 Jul 2016 16:06:00 GMT\r\nEtag: "c561c68d0ba92bbeb8b0f612a9199f722e3a621a"\r\nKeep-Alive: timeout=60, max=997\r\nServer: Apache\r\n\r\n%s"""

	async def send(self, data):
		#print('send %s' % data)
		if self.error is not None:
			return b''
		await self.send_q.put(data)

	async def recv(self):
		#print('recv in ')
		if self.error is not None:
			return b''
		try:
			data = await self.recv_q.get()
			return data
		except Exception as e:
			print('recv %s' % e)
			return b''

	async def close(self):
		if self.incoming_task is not None:
			self.incoming_task.cancel()
		if self.recv_q is not None:
			await self.recv_q.put(None)
		if self.send_q is not None:
			await self.send_q.put(None)

	async def __incoming_handle(self):
		try:
			while True:
				ibuff = b''
				remaining_bytes = 4096
				data = b''
				while remaining_bytes > 0:
					if len(ibuff) > 1024*1024*10:
						raise Exception('Incoming data too large!')
					temp = await self.reader.read(remaining_bytes)
					if temp == b'':
						await self.recv_q.put(None)
						return
					ibuff += temp
					#print(ibuff)
					if ibuff.find(b'\r\n\r\n') != 0:
						hdr, data = ibuff.split(b'\r\n\r\n', 1)
						headers = {}
						headers_lower = {}
						t_headers = hdr.split(b'\r\n')
						if t_headers[0].startswith(b'POST') is False:
							raise Exception('Not post request!')
						for h in t_headers[1:]:
							#print(h)
							key, value = h.split(b': ',1)
							key = key.decode('ascii')
							headers[key] = value
							headers_lower[key.lower()] = value
						#print(headers)

						if 'content-length' in headers_lower:
							data_length = int(headers_lower['content-length'])
							#print('data %s' % data)
							#print('lendata %s' % len(data))
							#print(data_length)
							if len(data) >= data_length:
								break
							remaining_bytes =  data_length - len(data)
						else:
							remaining_bytes = 0
				print('DD %s' % data)
				if len(data) > 5:

					data = base64.b64decode(urllib.parse.unquote(data[5:].decode()).encode())
					#print(data)
					await self.recv_q.put(data)

				try:
					senddata = await asyncio.wait_for(self.send_q.get(), 0.1)
				except asyncio.TimeoutError:
					#print('senddata %s ' % senddata )
					response = self.template % (b'0', b'')
				else:
					senddata = base64.b64encode(senddata)
					print('senddata %s ' % senddata )
					response = self.template % (str(len(senddata)).encode(), senddata)
				#print(response)
				self.writer.write(response)
				await self.writer.drain()


		except Exception as e:
			print('__incoming_handle %s' % e)
			import traceback
			traceback.print_exc()
			await self.close()
		finally:
			self.writer.close()


	async def run(self):
		self.send_q = asyncio.Queue()
		self.recv_q = asyncio.Queue()
		#self.incoming_task = asyncio.create_task(self.__incoming_handle())


class HTTP11TransportServer:
	def __init__(self, listen_ip, listen_port, logging_queue, ssl_ctx = None):
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.ssl_ctx = ssl_ctx
		self.logger = Logger('HTTP11TransportServer', logQ = logging_queue)
		self.agent_dispatch_queue = None #will be defined by the server!
		self.server = None
		self.agent_temp = {} #agent's own made-up ids -> transport

	@mpexception
	async def terminate(self):
		if self.server is not None:
			self.server.close()		
		if self.logger is not None:
			await self.logger.terminate()

	async def process_request(self, reader, writer):
		try:
			ibuff = b''
			remaining_bytes = 4096
			data = b''
			headers_lower = {}
			headers = {}

			while remaining_bytes > 0:
				if len(ibuff) > 1024*1024*10:
					raise Exception('Incoming data too large!')
				temp = await reader.read(remaining_bytes)
				if temp == b'':
					return
				ibuff += temp
				#print(ibuff)
				if ibuff.find(b'\r\n\r\n') != 0:
					hdr, data = ibuff.split(b'\r\n\r\n', 1)
					headers = {}
					
					t_headers = hdr.split(b'\r\n')
					if t_headers[0].startswith(b'POST') is False:
						raise Exception('Not post request!')
					for h in t_headers[1:]:
						#print(h)
						key, value = h.split(b': ',1)
						key = key.decode('ascii')
						headers[key] = value
						headers_lower[key.lower()] = value
					#print(headers)

					if 'content-length' in headers_lower:
						data_length = int(headers_lower['content-length'])
						#print('data %s' % data)
						#print('lendata %s' % len(data))
						#print(data_length)
						if len(data) >= data_length:
							break
						remaining_bytes =  data_length - len(data)
					else:
						remaining_bytes = 0
			
			#print('data %s' % data)
			if 'agentid' not in headers_lower:
				return
			
			if headers_lower['agentid'] not in self.agent_temp:
				packetizer = Packetizer(self.logger.logQ) # packetizer must be created here, because it's parameters will change based on the transport!
				transport = HTTP11Transport(reader, writer)
				await transport.run()
				self.agent_temp[headers_lower['agentid']] = transport
				agent = MultiplexorAgent(self.logger.logQ, transport, packetizer)
				await agent.run()
				await self.agent_dispatch_queue.put((agent, 'CONNECTED'))
				#await agent.wait_closed()
				#await self.logger.info('Agent disconnected! %s:%s' % (remote_ip, remote_port))
				#await self.agent_dispatch_queue.put((agent, 'DISCONNECTED'))

			transport = self.agent_temp[headers_lower['agentid']]
			#print('DD %s' % data)
			if len(data) > 5:

				data = base64.b64decode(urllib.parse.unquote(data[5:].decode()).encode())
				#print(data)
				await transport.recv_q.put(data)

			try:
				senddata = await asyncio.wait_for(transport.send_q.get(), 0.1)
			except asyncio.TimeoutError:
				#print('senddata %s ' % senddata )
				response = transport.template % (b'0', b'')
			else:
				senddata = base64.b64encode(senddata)
				#print('senddata %s ' % senddata )
				response = transport.template % (str(len(senddata)).encode(), senddata)
			#print(response)
			writer.write(response)
			await writer.drain()
			writer.close()

		except Exception as e:
			print('__incoming_handle %s' % e)
			import traceback
			traceback.print_exc()
		finally:
			writer.close()
	
	@mpexception
	async def handle_agent(self, reader, writer):
		"""
		This function gets invoked on each websocket connection.
		It creates an agenthandler with it's own packetizer, then notifies the server of the new agent's existense via the agent_dispatch_queue
		"""
		remote_ip, remote_port = writer.get_extra_info('peername')
		await self.logger.info('Agent connected from %s:%s' % (remote_ip, remote_port))
		await self.process_request(reader, writer)
		
	@mpexception
	async def run(self):
		self.server = await asyncio.start_server(self.handle_agent, self.listen_ip, self.listen_port, ssl=self.ssl_ctx)
		await self.server.wait_closed()