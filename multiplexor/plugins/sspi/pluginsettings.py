import json

class SSPIPluginServerStartupSettings:
	def __init__(self, listen_ip = None, listen_port = None, remote = False):
		#mandatory settings parameters
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.remote = remote
		
		
	def to_dict(self):
		return {
			'listen_ip'   : str(self.listen_ip) ,
			'listen_port' : str(self.listen_port) ,
			'remote'      : self.remote,
		}
	def to_json(self):
		return json.dumps(self.to_dict())
		

#if you modify the class below you'll need to modify the agent as well!
class SSPIPluginAgentStartupSettings:
	def __init__(self, operator_token = None):
		self.operator_token = operator_token #must be string!
		
	@staticmethod
	def from_dict(d):
		return SSPIPluginAgentStartupSettings(d.get('operator_token'))
		
	def to_dict(self):
		return {
			'operator_token'   : str(self.operator_token) ,
		}
	def to_json(self):
		return json.dumps(self.to_dict())
		
	def to_list(self):
		return [self.operator_token]

