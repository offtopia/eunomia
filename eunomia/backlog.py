from timetools import TimeTools

class BacklogItem:
	def __init__(self, message, timestamp):
		self.message = message
		self.timestamp = TimeTools.truncate_ns(timestamp)
		self.votes = 0
		self.legislated = False
		self.can_legislate = True
