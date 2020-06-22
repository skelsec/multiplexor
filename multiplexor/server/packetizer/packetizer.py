import asyncio
from multiplexor.logger.logger import *
from multiplexor.server.protocol.protocol import *

class Packetizer:
	def __init__(self, logQ):
		self.logger = Logger('Packetizer', logQ = logQ)
		self.packetizer_in = asyncio.Queue()
		self.packetizer_out = asyncio.Queue()
		self.multiplexor_in = asyncio.Queue()
		self.multiplexor_out = asyncio.Queue()
		self.recv_buffer = b''
		self.next_cmd_length = -1
		self.send_buffer = b''

		self.send_loop_task = None
		self.recv_loop_task = None
		
		
		self.max_packet_size = 5*1024

	@mpexception
	async def terminate(self):
		if self.multiplexor_in is not None:
			await self.multiplexor_in.put(None)
		if self.multiplexor_out is not None:
			await self.multiplexor_out.put(None)
		if self.send_loop_task is not None:
			self.send_loop_task.cancel()
		if self.recv_loop_task is not None:
			self.recv_loop_task.cancel()
		
		if self.logger is not None:
			await self.logger.terminate()
		
	@mpexception
	async def recv_loop(self):
		while True:
			#print('Waiting for incoming data from transport...')
			try:
				data = await self.packetizer_in.get()
				if data is None:
					await self.terminate()
					return
				self.recv_buffer += data
				await self.process_recv_buffer()
			
			except asyncio.CancelledError:
				return

	@mpexception			
	async def process_recv_buffer(self):
		if len(self.recv_buffer) < 4:
			return
				
		if self.next_cmd_length == -1:
			self.next_cmd_length = int.from_bytes(self.recv_buffer[:4], 'big', signed = False)
			#print('data length: %s' % self.next_cmd_length)
			
		if len(self.recv_buffer) >= self.next_cmd_length + 4 and self.next_cmd_length != -1:
			#rint('buffer: %s' % self.recv_buffer)
			cmd = MultiplexorCMD.from_bytes(self.recv_buffer[4: self.next_cmd_length + 4])
			#print(self.recv_buffer[: self.next_cmd_length + 4])
			self.recv_buffer = self.recv_buffer[self.next_cmd_length + 4:]
			self.next_cmd_length = -1
			#await self.logger.debug("Recieved reply: %s" % cmd)
			await self.multiplexor_in.put(cmd)
			await asyncio.sleep(0)
			await self.process_recv_buffer()
	
	@mpexception	
	async def send_loop(self):
		while True:
			cmd = await self.multiplexor_out.get()		
			#await self.logger.debug("Sending command: %s" % cmd)
			data = cmd.to_bytes()
			self.send_buffer += len(data).to_bytes(4, 'big', signed = False) + data
			
			if len(self.send_buffer) > self.max_packet_size:
				while len(self.send_buffer) > self.max_packet_size:
					await self.packetizer_out.put(self.send_buffer[:self.max_packet_size])
					self.send_buffer = self.send_buffer[self.max_packet_size:]
					await asyncio.sleep(0)
					
			if len(self.send_buffer) > 0:
				await self.packetizer_out.put(self.send_buffer)
				await asyncio.sleep(0)
				self.send_buffer = b''
					
	@mpexception	
	async def run(self):
		self.send_loop_task = asyncio.create_task(self.send_loop())
		self.recv_loop_task = asyncio.create_task(self.recv_loop())