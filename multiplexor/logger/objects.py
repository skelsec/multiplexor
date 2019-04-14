import json
import enum
import datetime
import time

class LogObjectType(enum.Enum):
	LOGENTRY = 0
	REMOTELOG = 10

	
class RemoteLog:
	def __init__(self, rlog):
		self.remote_ip = rlog.remote_ip
		self.remote_port = rlog.remote_port
		self.client_id = rlog.client_id
		self.log_obj = logobj2type[LogObjectType(rlog.log_obj_type)].from_dict(rlog.log_obj)
		
	def __str__(self):
		return "[%s][%s:%s] %s" % (self.client_id, self.remote_ip, self.remote_port, str(self.log_obj))

	def to_dict(self):
		t = {}
		t['remote_ip'] = self.remote_ip
		t['remote_port'] = self.remote_port
		t['client_id'] = self.client_id
		t['log_obj'] = self.log_obj.to_dict()
		return t 

	def to_json(self):
		return json.dumps(self.to_dict(), cls=UniversalEncoder)
		
class LogEntry:
	"""
	Communications object that is used to pass log information to the LogProcessor
	"""
	def __init__(self, level, name, msg, agent_id = None):
		"""

		:param level: log level
		:type level: int
		:param name: name of the module emitting the message
		:type name: str
		:param msg: the message which will be logged
		:type msg: str
		"""
		self.level = level
		self.name  = name
		self.msg   = msg
		self.agent_id = agent_id

	def to_dict(self):
		t = {}
		t['level'] = self.level
		t['name'] = self.name
		t['msg'] = self.msg
		t['agent_id'] = self.agent_id
		return t

	def to_json(self):
		return json.dumps(self.to_dict(), cls=UniversalEncoder)

	def __str__(self):
		t = '[%s]' % self.name
		t += ' %s' % self.msg

		return t

		
	@staticmethod
	def from_dict(d):
		return LogEntry( d['level'], d['name'], d['msg'], None)
		
		
	@staticmethod
	def from_json(data):
		return LogEntry.from_dict(json.loads(data))



### needs to be at the bottom!!!
logobj2type = {
	LogObjectType.LOGENTRY : LogEntry,
}

logobj2type_inv = {v: k for k, v in logobj2type.items()}

def get_rdns_tld(rdns):
	if not rdns:
		return None
	m = rdns.rfind(".")
	if m == -1:
		return None
	return rdns[m+1:]