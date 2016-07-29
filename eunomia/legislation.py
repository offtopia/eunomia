"""
.. module:: legislation
	:platform: Unix
	:synopsis: Handles all of eunomia's legislation/vote tracking features.

.. moduleauthor:: Nicholas De Nova <nanovad@gmail.com>

"""

import logging
from enum import Enum

from re import compile as regex

vote_matcher = regex(r'<[^>]+> (?:(?P<nick>\S+)[:,] )?:D(?:(?P<carots>\^+)|~(?P<ints>\d+)|~(?P<expr>.+))?$')

class Legislation:
	""" Class that contains all legislation related functions.

		:param fhandler: Logging handler for output to a file.
		:type fhandler: logging.FileHandler
		:param shandler: Logging handler for output to a stream.
		:type shandler: logging.StreamHandler
	"""

	def __init__(self, fhandler, shandler):
		self.logger = logging.getLogger("Legislation")
		self.logger.setLevel(logging.DEBUG)

		self.logger.addHandler(fhandler)
		self.logger.addHandler(shandler)

		self.logger.info("Init complete.")

		self.active_proposal = None

	def is_non_proposal_filibuster(self, message):
		""" Parses the message, determines if it is a filibustering non-proposal (D: or :D:)

			:param message: Message to parse.
			:type message: str
			:returns: True if the message is 'D:', ':D:', or 'nick: D:', etc.
		"""

		npf_matcher = regex(r'<[^>]+> (?:(\S+)[:,] )?(:)?D:')
		result = npf_matcher.match(message)

		return False if result == None else True

	def is_ignored_message(self, message):
		""" Parses the message, determines if it should be ignored (does not reset votecount, is not a proposal)

			:param message: Message to parse.
			:type message: strings
			:returns: True if the message should be ignored when legislating.
		"""

		jpq_matcher = regex(r'\*\*\* (Joins|Parts|Quits)')
		result = jpq_matcher.match(message)

		return False if result == None else True

	def get_packed_vote_index(self, message):
		""" Parses the message, determines if it's a vote or not, and returns various information about the type of vote and its attributes.

			:param message: Message to parse.
			:type message: str
			:returns: A tuple, containing nick (or None), and, if applicable, and a backreference index, if applicable. Alternatively, returns None if the message was not matched to a known form of vote.
		"""
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
		"""
			Parses message and determines if it is a vote or proposal.
			If it is a vote, determines type of vote, and dereferences the proposal the vote refers to.
			If it is not a vote, saves the index of the proposal in the backlog.

			If 3 votes are counted, legislates the pending proposal, see :func:`eunomia.legislation.Legislation.legislate`

			:param message: A tuple containing both the message in string format and the timestamp.
			:param backlog: A potentially modified backlog (this is used during recursion; when the backlog is sliced to avoid recounting votes.)
			:param backlog_orig: An original copy of the backlog, used mostly for context inthe event of a successful legislation.
			:param votecount: Number of votes already counted during recursion.
			:type message: tuple
			:type backlog: list
			:type backlog_orig: list
			:type votecount: int
		"""

		(raw_message, timestamp) = message

		self.logger.debug("Message \"{}\" dereferencing...".format(raw_message))

		if self.is_non_proposal_filibuster(raw_message):
			# Because non proposal filibusters are not true proposals they cannot be dereferenced.
			votecount = 0
			return

		if self.is_ignored_message(raw_message):
			# Just ignore and recurse further.
			self.dereference_if_vote(backlog[-2], backlog[:-1], backlog_orig, votecount)
			return

		packed = self.get_packed_vote_index(raw_message)
		if packed == None:
			# It's a proposal
			self.active_proposal = len(backlog) - 1
			if votecount == 3:
				self.legislate(backlog[self.active_proposal], backlog_orig[-25:])
			return

		(nick, back_x) = packed

		if nick == None:
			if back_x == 0:
				# It's a basic :D
				self.logger.debug("Basic :D.")
				self.dereference_if_vote(backlog[-2], backlog[:-1], backlog_orig, votecount + 1)
			else:
				self.logger.debug(":D~expr/:D~N")
				try:
					self.dereference_if_vote(backlog[-back_x - 2], backlog, backlog_orig, votecount + 1)
				except IndexError as e:
					self.logger.exception(":D~expr dereferencing failed! It is likely that the expr is out-of-bounds in the backlog.")
		else:
			self.logger.debug("nick: :D")

			votecount += 1

			nick_msgs = 0
			for i in range(len(backlog) - 1, -1, -1):
				if backlog[i][0].startswith("<{}>".format(nick)):
					# Messages are only counted if they're not a vote.
					# self.get_packed_vote_index returns None if the message is not a vote.
					# If it does not return None, just pass over the message.
					if self.get_packed_vote_index(backlog[i][0]) != None:
							pass

					# If we made it here, the message is not a vote and should be counted.

					if nick_msgs == back_x:
						self.active_proposal = i
					nick_msgs += 1

			if votecount == 3:
				self.legislate(backlog[self.active_proposal], backlog_orig[-25:])

		if self.active_proposal != None:
			self.active_proposal += 1

	def legislate(self, message, context):
		""" Legislates a given message and context, writes these to file ``pending_proposals.txt``

			Does **not** check if there were sufficient votes - it is up to the caller to determine this **before** ``legislate`` is called.

			:param message: The message that was legislated.
			:param context: The 'context' (backlog, preferably including votes) around the legislated message.
			:type message: str
			:type context: list
		"""

		self.logger.info("Legislation for proposal \"{}\" succeeded.".format(message))

		(raw_message, timestamp) = message
		f = open("pending_proposals.txt", "a")
		f.write("[{}]\n".format(raw_message))
		for line in context:
			(raw_line, timestamp) = line
			f.write("{} {}\n".format(str(timestamp), raw_line))
		f.write("\n") # Write one last newline.
		f.close()

		self.active_proposal = None
		self.active_votes = 0
