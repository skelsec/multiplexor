import enum

class PluginType(enum.Enum):
	"""
	Extend this enum when new types are implemented!
	"""
	SOCKS5 = 0
	SSPI = 1