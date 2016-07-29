import datetime
import os

class RolloverLogger:
	def __init__(self, log_type_name, log_subdirs=None):
		self.log_dir = os.path.dirname(os.path.dirname(__file__)) + "/logs/{}".format(log_type_name)

		if log_subdirs != None:
			# If there are extra subdirs, append them.
			print("Formatting with log subdirs: " + str(log_subdirs))
			self.log_dir = "{}/{}".format(self.log_dir, log_subdirs)

		print("Log dir is now " + str(self.log_dir))

		# Also initialize the current date.
		self.date_now = self.get_current_date()

	def get_current_date(self):
		datetime_now = datetime.datetime.utcnow()
		return datetime.date(datetime_now.year, datetime_now.month, datetime_now.day)

	def update_current_date(self):
		# TODO: This could probably just be 'self.date_now = self.get_current_date()'.
		date_new = self.get_current_date()

		if date_new == self.date_now:
			# There's no need to change the date - we're already up to date.
			return

		self.date_now = date_new

	def update_log_filename(self):
		# Make sure the date is correct.
		self.update_current_date()

		# Create the log dir (recursively) if it does not exist.
		if not os.path.exists(self.log_dir):
			os.makedirs(self.log_dir)

		self.log_filename = "{}/{}.log".format(self.log_dir, self.date_now)

	def append(self, log_message):
		# Make sure that we're writing to the right logfile.
		self.update_log_filename()

		# We assume log_message is already preformatted.
		# This is basically a stub to append to the file right now.
		with open(self.log_filename, 'a') as logfile:
			logfile.write(log_message)

class ChannelLogger(RolloverLogger):
	def __init__(self, channel_name):
		self.channel_name = channel_name

		super().__init__("channel", channel_name)
