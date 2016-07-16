import logging
from enum import Enum

class ProposalType(Enum):
	BASIC = 1
	NBACK = 2
	NCIRCUMFLEX = 3
	NEXPRESSION = 4
	KICK = 5

	PREFIXED_BASIC = 6
	PREFIXED_NBACK = 7
	PREFIXED_NCIRCUMFLEX = 8
	PREFIXED_NEXPRESSION = 9

class Legislation:
	def __init__(self, fhandler, shandler):
		self.logger = logging.getLogger("Legislation")
		self.logger.setLevel(logging.INFO)

		self.logger.addHandler(fhandler)
		self.logger.addHandler(shandler)

		self.logger.info("Init complete.")

	def is_proposal(self, message):
		# TODO: Implement checking for bot replies, nolog
		if not self.is_basic_vote(message):
			return True
	
	def is_basic_vote(self, message):
		# TODO: Proper vote detection/evaluation.
		if message == ":D":
			return True
		else:
			return False
	
	def find_last_proposal_index(self, backlog):
		# Since EunomiaBot uses 0-max as oldest-newest, we assume that's the format backlog is in and traverse accordingly.
		self.logger.debug("Backlog length {}".format(len(backlog)))

		# range(1, 0, -1) steps down from 1 to 0. However, it is end-bounding exclusive, so use range(1, -1, -1) in order to get [1, 0].

		# For some reason, range(0, -1, -1) returns an empty range object.
		# This is a workaround for that.
		brange = list(range(len(backlog) - 1, -1, -1))
		print(brange)
		if not brange:
			self.logger.debug("brange is empty. This is likely to happen if there is only one item in the backlog. Setting to [0].")
			brange = [0]
		for i in brange:
			message = backlog[i]
			if self.is_proposal(message):
				self.logger.debug("\"{}\" is proposal at index {}".format(message, i))
				return i
		
		return -1

	def legislate_basic_vote_proposal(self, message):
		
