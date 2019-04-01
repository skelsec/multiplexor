import asyncio

class Packetizer:
	def __init__(self, agent_id, cancellation_evt):
		self.agent_id = agent_id
		self.trasnport_terminated_evt = cancellation_evt
		self.packetizer_in = asyncio.Queue()
		self.packetizer_out = asyncio.Queue()
		self.multiplexor_in = asyncio.Queue()
		self.multiplexor_out = asyncio.Queue()
		self.recv_buffer = b''
		self.next_cmd_length = -1
		self.send_buffer = b''
		
		
		self.max_packet_size = 5*1024
		
	async def recv_loop(self):
		while not self.trasnport_terminated_evt.is_set():
			data = await self.packetizer_in.get()
			self.recv_buffer += data
			await self.process_recv_buffer()
			
				
	async def process_recv_buffer(self):
		if len(self.recv_buffer) != 4:
			return
				
		if self.next_cmd_length == -1:
			self.next_cmd_length = int.from_bytes(self.recv_buffer[:4], 'big', signed = False)
			
		if len(self.recv_buffer) >= self.next_cmd_length + 4:
			cmd = PYPYCMD.from_bytes(self.recv_buffer[: self.next_cmd_length + 4])
			self.recv_buffer = self.recv_buffer[self.next_cmd_length + 4:]
			await self.multiplexor_in.put((agent_id, cmd))
			await self.process_recv_buffer(self)
		
	async def send_loop(self):
		while not self.trasnport_terminated_evt.is_set():
			try:
				cmd = await asyncio.wait_for(self.multiplexor_out.get(), timeout = 1)					
			except TimeoutError:
				if len(self.send_buffer) > 0:
					await self.packetizer_out.put(self.send_buffer)
					continue
							
			self.send_buffer += cmd.to_bytes()
			
			if len(self.send_buffer) > self.max_packet_size:
				while not self.trasnport_terminated_evt.is_set() and len(self.send_buffer) > self.max_packet_size:
					await self.packetizer_out.put(self.send_buffer[:self.max_packet_size])
					self.send_buffer = self.send_buffer[self.max_packet_size:]
					
		
	async def run(self):
		asyncio.ensure_future(self.recv_loop())
		asyncio.ensure_future(self.send_loop())