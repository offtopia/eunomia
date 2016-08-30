"""
.. module:: legislation
	:platform: Unix
	:synopsis: Handles all of eunomia's legislation/vote tracking features.

.. moduleauthor:: Nicholas De Nova <nanovad@gmail.com>

"""

import logging
import eunomialog

from backlog import BacklogItem

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

	def __init__(self, fhandler, shandler, channel):
		self.logger = logging.getLogger("Legislation")
		self.logger.setLevel(logging.INFO)

		self.logger.addHandler(fhandler)
		self.logger.addHandler(shandler)

		self.logger.info("Init complete.")

		self.active_proposal = None
		self._votecount = 0
		self.votecount = 0

		self.proposal_logger = eunomialog.ProposalLogger(channel)

	@property
	def votecount(self):
		return self._votecount
	@votecount.setter
	def votecount(self, value):
		self.logger.debug("Votecount previously {}, now {}".format(self.votecount, value))
		self._votecount = value
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

	def dereference_if_vote(self, message, backlog):
		# Step backwards, from newest to oldest messages, one at a time.
		for i in range(len(backlog) - 1, -1, -1):
			self.logger.debug("At backlog position " + str(i))
			current_message = backlog[i].message
			self.logger.debug("Current message=" + current_message)

			packed = self.get_packed_vote_index(current_message)

			if packed == None:
				self.logger.debug("packed==None")
				self.votecount = 0
				return
			else:
				(nick, back_x) = packed
				if nick == None:
					if back_x == 0:
						self.logger.debug("Basic ':D'")
						self.votecount += 1
						""" Active proposal is not set here.
	                        If it were, it would break 'nick: :D' referencing (and probably other things.)
                        	Also, it's pointless - either the referencing will be covered in
                        	the amount of backlog to be stored, or the reference will be stored properly
                        	by a 'more complex' reference (like 'nick: :D')
                        """
					else:
						self.logger.debug("':D~expr/:D~N'")
						self.votecount += 1
				else:
					self.logger.debug("'nick: :D'")
					nick_messages = 0
					for i in range(len(backlog) - 1, -1, -1):
						self.logger.debug("Indexing... ({})".format(str(i)))
						message = backlog[i].message
						if message.startswith("<{}>".format(nick)) or message.startswith("* {}".format(nick)) and (self.get_packed_vote_index(message) != None and back_x == 0):
							self.logger.debug("Target \"{}\" found.".format(nick))
							if nick_messages == back_x:
								if i == self.active_proposal:
									self.logger.debug("Incrementing proposal.")
									self.votecount += 1
								else:
									self.logger.debug("Changing proposal. Setting votecount to 1.")
									self.active_proposal = i
									self.votecount = 1

							nick_messages += 1

			self.logger.debug("votecount=" + str(self.votecount))
			self.logger.debug("active_proposal=" + str(self.active_proposal))
			if self.votecount == 3:
				if self.active_proposal == None:
					self.active_proposal = len(backlog) - 1
				# self.legislate() sets self.votecount to 0, so we don't need to worry about it.
				self.legislate(backlog[self.active_proposal], backlog[self.active_proposal - 25:])
				return

		# Cleanup
		self.votecount = 0

	def legislate(self, message, context):
		""" Legislates a given message and context, writes these to file ``pending_proposals.txt``

			Does **not** check if there were sufficient votes - it is up to the caller to determine this **before** ``legislate`` is called.

			:param message: The message that was legislated.
			:param context: The 'context' (backlog, preferably including votes) around the legislated message.
			:type message: str
			:type context: list
		"""

		self.logger.info("Legislation for proposal \"{}\" succeeded.".format(message.message))

		# NOTE: RolloverLogger (which ProposalLogger inherits) writes lists item-by-item, with a newline after each.
		# So we don't need to append newlines here.

		# Because BacklogItems are used now, just unpack the 'message' field.
		raw_message = message.message

		output = []
		output.append("[{}]".format(raw_message))
		for line in context:
			output.append("{} {}".format(line.timestamp, line.message))

		self.proposal_logger.append(output)

		self.active_proposal = None
		self.votecount = 0
