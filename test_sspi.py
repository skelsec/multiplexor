import asyncio

from multiplexor.operator.operator import Operator

if __name__ == '__main__':
	operator = Operator()
	
	loop = asyncio.get_event_loop()
	loop.run_until_complete(operator.send_test_sspi())