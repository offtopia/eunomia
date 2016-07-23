import logging
from enum import Enum

from re import compile as regex

vote_matcher = regex(r'<[^>]+> (?:(?P<nick>\S+)[:,] )?:D(?:(?P<carots>\^+)|~(?P<ints>\d+)|~(?P<expr>.+))?$')

class Legislation:
	def __init__(self, fhandler, shandler):
		self.logger = logging.getLogger("Legislation")
		self.logger.setLevel(logging.DEBUG)

		self.logger.addHandler(fhandler)
		self.logger.addHandler(shandler)

		self.logger.info("Init complete.")

	def get_packed_vote_index(self, message):
		match = vote_matcher.match(message)
		if match is None:
			return None
			
		match = match.groupdict()
		if match['ints'] is not None:
			return (match['nick'], int(match['ints']))
		elif match['carots'] is not None:
			return (match['nick'], len(match['carots']))
		elif match['expr'] is not None:
			pass

		return (match['nick'], 0)

	def dereference_if_vote(self, message, backlog, backlog_orig, votecount=0):
		self.logger.debug("Message \"{}\" dereferencing...".format(message))
		packed = self.get_packed_vote_index(message)
		if packed == None:
			# It's a proposal.
			self.logger.debug("It's a proposal.")
			if votecount == 3:
				self.legislate(message, backlog_orig[-25:])
			return message

		(nick, back_x) = packed
		if nick == None and back_x == 0:
			self.logger.debug("It's a basic :D. Dereferencing by recursion.")
			return self.dereference_if_vote(backlog[len(backlog) - 2], backlog[:-1], backlog_orig, votecount + 1)

		else:
			self.logger.debug("It's a nick: :D or :D~expr. Dereferencing by recursion.")
			if votecount == 3:
				self.legislate(message, backlog_orig[-25:])
			return self.dereference_if_vote(backlog[len(backlog) - back_x - 1], backlog[:-1], backlog_orig, votecount + 1)
	
	def legislate(self, message, context):
		self.logger.info("Legislation for proposal \"{}\" succeeded.".format(message))
		f = open("pending_proposals.txt", "a")
		f.write("[{}]\n".format(message))
		for line in context:
			f.write("{}\n".format(line))
		f.write("\n") # Write one last newline.
		f.close()
