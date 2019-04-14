import json

class Socks5PluginServerStartupSettings:
	def __init__(self, listen_ip = None, listen_port = None, auth_type = None, remote = False):
		#mandatory settings parameters
		self.listen_ip = listen_ip
		self.listen_port = listen_port
		self.remote = remote
		
		#socks5 specific parameters
		self.auth_type = auth_type
		
		
	def to_dict(self):
		return {
			'listen_ip'   : str(self.listen_ip) ,
			'listen_port' : str(self.listen_port) ,
			'auth_type'   : self.auth_type ,
			'remote'      : self.remote,
		}
	def to_json(self):
		return json.dumps(self.to_dict())
		

#if you modify the class below you'll need to modify the agent as well!
class Socks5PluginAgentStartupSettings:
	def __init__(self, operator_token = None):
		self.operator_token = operator_token #must be string!
		
	@staticmethod
	def from_dict(d):
		return Socks5PluginAgentStartupSettings(d.get('operator_token'))
		
	def to_dict(self):
		return {
			'operator_token'   : str(self.operator_token) ,
		}
	def to_json(self):
		return json.dumps(self.to_dict())
		
	def to_list(self):
		return [self.operator_token]

