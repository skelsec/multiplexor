import logging
import traceback
import sys
import io
import asyncio

from multiplexor.logger.objects import *

class Logger:
	"""
	This class is used to provie a better logging experience for asyncio based classes/functions
	Probably will replace logtask "solution" with this one in the future
	sink: logging object to have unified logging
	TODO
	"""
	def __init__(self, name, logQ = None, sink = None):
		self.consumers = {}
		self.name = name
		self.sink = sink
		self.is_running = False
		self.logging = logging #.getLogger('__multiplexor__.' + self.name )

		self.is_final = True
		if logQ:
			self.logQ = logQ
			self.is_final = False
		else:
			self.logQ = asyncio.Queue()

	async def terminate(self):
		print('terminate called!')
		#TODO: implement
		return
		
	async def run(self):
		"""
		you only need to call this function IF the logger instance is the final dst!
		Also, consumers will not work if this is not the final one!
		"""
		if self.is_final == False:
			return
		if self.is_running == True:
			return
		try:
			self.is_running = True
			while True:
				logmsg = await self.logQ.get()
				await self.handle_logger(logmsg)
				if len(self.consumers) > 0:
					await self.handle_consumers(logmsg)
		except asyncio.CancelledError:
			return
		except Exception as e:
			print('Logger run exception! %s' % e)
			
	async def handle_logger(self, msg):
		if self.sink is None:
			self.logging.log(msg.level, '%s %s %s' % (datetime.datetime.utcnow().isoformat(), self.name, msg.msg))
		else:
			self.sink.log(msg.level, '%s %s' % (self.name, msg.msg))
		
	async def handle_consumers(self, msg):
		try:
			for consumer in self.consumers:
				await consumer.process_log(msg)
		except Exception as e:
			print(e)
			
	async def debug(self, msg):
		await self.logQ.put(LogEntry(logging.DEBUG, self.name, msg))
		
	async def info(self, msg):
		await self.logQ.put(LogEntry(logging.INFO, self.name, msg))
	
	async def exception(self, message = None):
		sio = io.StringIO()
		ei = sys.exc_info()
		tb = ei[2]
		traceback.print_exception(ei[0], ei[1], tb, None, sio)
		msg = sio.getvalue()
		if msg[-1] == '\n':
			msg = msg[:-1]
		sio.close()
		if message is not None:
			msg = '%s : %s' % (message,msg)
		await self.logQ.put(LogEntry(logging.ERROR, self.name, msg))
			
	async def error(self, msg):
		traceback.print_stack()
		await self.logQ.put(LogEntry(logging.ERROR, self.name, msg))
		
	async def warning(self, msg):
		await self.logQ.put(LogEntry(logging.WARNING, self.name, msg))
		
	async def log(self, level, msg):
		"""
		Level MUST be bigger than 0!!!
		"""
		await self.logQ.put(LogEntry(level, self.name, msg))

		
	def add_consumer(self, consumer):
		self.consumers[consumer] = 0
		
	def del_consumer(self, consumer):
		if consumer in self.consumers:
			del self.consumers[consumer]
			
			
def mpexception(funct):
	"""
	Decorator for handling exceptions
	Use it with the Logger class only!!!
	"""
	async def wrapper(*args, **kwargs):
		this = args[0] #renaming self to 'this'
		try:
			t = await funct(*args, **kwargs)
			return t
		except asyncio.CancelledError:
			return
		except Exception as e:
			await this.logger.exception(funct.__name__)
			raise e
			
	return wrapper