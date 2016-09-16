import datetime
import os

class RolloverLogger:
	"""	Provides a basic class for logging that creates new logfiles based on date.
	"""
	def __init__(self, log_type_name, log_subdirs=None):
		self.log_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + "/logs/{}".format(log_type_name)

		if log_subdirs != None:
			# If there are extra subdirs, append them.
			self.log_dir = "{}/{}".format(self.log_dir, log_subdirs)

		# Also initialize the current date.
		self.date_now = self.get_current_date()

	def get_current_date(self):
		""" Gets the current UTC date.

			:returns: A :class:`datetime.date` object containing the current date.
			:rtype: datetime.date
		"""
		datetime_now = datetime.datetime.utcnow()
		return datetime.date(datetime_now.year, datetime_now.month, datetime_now.day)

	def update_current_date(self):
		""" Updates the current UTC date.
			Ignores if the date is current.
		"""
		# TODO: This could probably just be 'self.date_now = self.get_current_date()'.
		date_new = self.get_current_date()

		if date_new == self.date_now:
			# There's no need to change the date - we're already up to date.
			return

		self.date_now = date_new

	def update_log_filename(self):
		""" Updates the current log filename, making sure to use the correct file for the date.
		"""
		# Make sure the date is correct.
		self.update_current_date()

		# Create the log dir (recursively) if it does not exist.
		if not os.path.exists(self.log_dir):
			os.makedirs(self.log_dir)

		self.log_filename = "{}/{}.log".format(self.log_dir, self.date_now)

	def append(self, log_message):
		""" Appends a new line/list of lines to the log.

			If ``log_message`` is a ``str``, a newline is appended before it is written to the log.

			If ``log_message`` is a ``list``, a newline is appended to each item, then they are written to the log.

			:param log_message: Either a ``str`` to append to the log, or a ``list`` of strs to append.
			:type log_message: str/list
		"""
		# Make sure that we're writing to the right logfile.
		self.update_log_filename()

		# We assume log_message is already preformatted.
		# This is basically a stub to append to the file right now.
		# However, it is assumed that the log entry does not include trailing newline.
		with open(self.log_filename, 'a') as logfile:
			# Write all items, one by one, with newlines after each, if it's a list.
			if isinstance(log_message, list):
				for line in log_message:
					logfile.write(line + "\n")
			# Or if it's a string, just write the message with a trailing newline.
			elif isinstance(log_message, str):
				logfile.write(log_message + "\n")

class ChannelLogger(RolloverLogger):
	""" Handles logging of channel messages to disk.
	"""
	def __init__(self, channel_name):
		self.channel_name = channel_name

		super().__init__("channel", channel_name)

	# TODO: Unify timestamp formatting between this and the legislation module.

	def append_log_begin_message(self):
		time_now = datetime.datetime.utcnow()
		self.append("{:02d}:{:02d}:{:02d} --- log begin ---".format(time_now.hour, time_now.minute, time_now.second))

	def append_log_end_message(self):
		time_now = datetime.datetime.utcnow()
		self.append("{:02d}:{:02d}:{:02d} --- log end ---".format(time_now.hour, time_now.minute, time_now.second))

class ProposalLogger(RolloverLogger):
	""" Handles logging of proposals to disk.
	"""
	def __init__(self, channel_name):
		self.channel_name = channel_name

		super().__init__("proposal", channel_name)

	def get_current_time(self):
		datetime_now = datetime.datetime.utcnow()

		return datetime.time(datetime_now.hour, datetime_now.minute, datetime_now.second)

	def update_log_filename(self):
		super().update_log_filename()
		self.log_filename = "{}/{}_{}.log".format(self.log_dir, self.date_now, self.get_current_time())
