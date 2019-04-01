
class GenericTask:
	def __init__(self, recv_queue, send_queue, stop_evt):
		self.recv_queue = recv_queue
		self.send_queue = send_queue
		self.stop_evt = stop_evt
		
	def send(self, data):
		self.send_queue.put(data)
		
	def recv(self, data)
		self.recv_queue.put(data)
		
	def run(self):
		while not self.stop_evt.is_set():
			data = self.recv()
			self.send(data)
			
			
			
class GenericTaskHandler:
	def __init__(self, recv_queue, send_queue, log_queue, user_queue_in, user_queue_out, stop_evt):
		self.recv_queue = recv_queue
		self.send_queue = send_queue
		self.log_queue = log_queue
		self.user_queue_in = user_queue_in
		self.user_queue_out = user_queue_out
		self.stop_evt = stop_evt
	
	def send(self, data):
		self.send_queue.put(data)
		
	def recv(self, data)
		self.recv_queue.put(data)
		
	def run(self):
		while not self.stop_evt.is_set():
			user_cmd = user_queue_in.get()
			self.send(user_cmd.encode())
			data = self.recv()
			self.user_queue.out.put(data.decode())