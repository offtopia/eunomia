import datetime

class TimeTools:
	@staticmethod
	def truncate_ns(timestamp):
		return datetime.time(timestamp.hour, timestamp.minute, timestamp.second)
