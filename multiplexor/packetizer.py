import asyncio
from multiplexor.logger.logger import *
from multiplexor.protocol.server import *

class Packetizer:
	def __init__(self, logQ, cancellation_evt):
		self.logger = Logger('Packetizer', logQ = logQ)
		self.trasnport_terminated_evt = cancellation_evt
		self.packetizer_in = asyncio.Queue()
		self.packetizer_out = asyncio.Queue()
		self.multiplexor_in = asyncio.Queue()
		self.multiplexor_out = asyncio.Queue()
		self.recv_buffer = b''
		self.next_cmd_length = -1
		self.send_buffer = b''
		
		
		self.max_packet_size = 5*1024
		
	@mpexception
	async def recv_loop(self):
		while not self.trasnport_terminated_evt.is_set():
			print('Waiting for incoming dat from transport...')
			data = await self.packetizer_in.get()
			print('Data in: %s' % data)
			self.recv_buffer += data
			await self.process_recv_buffer()
			
	@mpexception			
	async def process_recv_buffer(self):
		if len(self.recv_buffer) < 4:
			return
				
		if self.next_cmd_length == -1:
			self.next_cmd_length = int.from_bytes(self.recv_buffer[:4], 'big', signed = False)
			print('data length: %s' % self.next_cmd_length)
			
		if len(self.recv_buffer) >= self.next_cmd_length + 4 and self.next_cmd_length != -1:
			cmd = MultiplexorCMD.from_bytes(self.recv_buffer[4: self.next_cmd_length + 4])
			print(self.recv_buffer[: self.next_cmd_length + 4])
			self.recv_buffer = self.recv_buffer[self.next_cmd_length + 4:]
			self.next_cmd_length = -1
			await self.logger.debug("Recieved reply: %s" % cmd)
			await self.multiplexor_in.put(cmd)
			await self.process_recv_buffer()
	
	@mpexception	
	async def send_loop(self):
		while not self.trasnport_terminated_evt.is_set():
			cmd = await self.multiplexor_out.get()		
			await self.logger.debug("Sending command: %s" % cmd)
			data = cmd.to_bytes()
			self.send_buffer += len(data).to_bytes(4, 'big', signed = False) + data
			
			if len(self.send_buffer) > self.max_packet_size:
				while not self.trasnport_terminated_evt.is_set() and len(self.send_buffer) > self.max_packet_size:
					await self.packetizer_out.put(self.send_buffer[:self.max_packet_size])
					self.send_buffer = self.send_buffer[self.max_packet_size:]
					await asuncio.sleep(0)
					
			if len(self.send_buffer) > 0:
				await self.packetizer_out.put(self.send_buffer)
					
	@mpexception	
	async def run(self):
		asyncio.ensure_future(self.recv_loop())
		asyncio.ensure_future(self.send_loop())