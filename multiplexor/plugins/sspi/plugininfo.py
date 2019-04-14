import json

class WinAPIPluginInfo:
	def __init__(self):
		self.listen_ip = None
		self.listen_port = None
		self.auth_type = None
		self.active_connections = {} #source addr - > dst_addr
		
	def to_dict(self):
		return {
			'listen_ip'   : str(self.listen_ip) ,
			'listen_port' : str(self.listen_port) ,
			'auth_type' : self.auth_type ,
			'active_connections' : self.active_connections ,
		}
	def to_json(self):
		return json.dumps(self.to_dict())