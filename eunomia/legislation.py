import logging

class Legislation:
	def __init__(self, fhandler, shandler):
		self.logger = logging.getLogger("Legislation")
		self.logger.setLevel(logging.INFO)

		self.logger.addHandler(fhandler)
		self.logger.addHandler(shandler)

		self.logger.info("Init complete.")
	
	def is_filibuster(self, message):
		# TODO: Check for filibustering.
		return False

	def is_vote(self, message):
		# TODO: Check for vote.
		return False
