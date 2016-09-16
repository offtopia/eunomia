import importlib
import signal
import sys

import irc.bot
import irc.strings
import logging
import legislation
import datetime
import eunomialog
from backlog import BacklogItem

class EunomiaBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, pretty_version, ident_packed=None, port=6667):
		self.logger = logging.getLogger("EunomiaBot")
		self.logger.setLevel(logging.INFO)

		lformat = logging.Formatter("[%(asctime)s] [%(name)s.%(funcName)s] [%(levelname)-5.5s]: %(message)s", "%Y-%m-%d %H:%M:%S")

		fh = logging.FileHandler("eunomia.log")
		fh.setFormatter(lformat)
		sh = logging.StreamHandler()
		sh.setFormatter(lformat)

		self.logger.addHandler(fh)
		self.logger.addHandler(sh)

		self.file_log_handler = fh
		self.stream_log_handler = sh

		self.logger.info("Logging initialized.")
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.channel = channel

		self.reloading = False

		self.logger.info("Init complete.")

		self.legislator = legislation.Legislation(fh, sh, channel)

		self.max_backlog_length = 50
		self.backlog = []

		self.channel_logger = eunomialog.ChannelLogger(channel)

		if ident_packed != None:
			(self.ident_username, self.ident_pass, self.ident_method) = ident_packed
		else:
			self.ident_username = self.ident_pass = self.ident_method = None

		self.pretty_version = pretty_version

		signal.signal(signal.SIGTERM, self.shutdown_handler)
		signal.signal(signal.SIGINT, self.shutdown_handler)

	def on_nicknameinuse(self, c, event):
		c.nick(c.get_nickname() + "_")
		self.logger.info("Nickname {} was in use. Trying {}.".format(c.get_nickname(), c.get_nickname() + "_"))

	def on_welcome(self, c, event):
		self.channel_logger.append_log_begin_message()
		
		c.join(self.channel)
		self.logger.info("Connection complete.")

		if self.ident_method != None:
			if self.ident_method == "nickserv":
				self.logger.info("Identifying to NickServ.")
				c.privmsg("NickServ", "identify {} {}".format(self.ident_username, self.ident_pass))
			else:
				self.logger.error("Identification method \"{}\" not supported.".format(self.ident_method))
			self.logger.info("Identification finished.")
		else:
			self.logger.info("Not identifying.")

	def on_privmsg(self, c, event):
		self.do_command(event, event.arguments[0])
		self.logger.info("Got a PRIVMSG: \"{}\"").format(event.arguments[0])

	def on_pubmsg(self, c, event):
		message = event.arguments[0]
		sender = event.source.split("!")[0]
		message = "<{}> {}".format(sender, message)

		timestamp = datetime.datetime.utcnow().time()

		mbi = self.message_to_backlog_item(message, timestamp)

		self.add_to_backlog(mbi, timestamp)

		self.backlog = self.legislator.dereference_if_vote(mbi, self.backlog)

		a = event.arguments[0].split(":", 1)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			command = a[1].strip()
			self.logger.info("Command \"{}\" sent by \"{}\"".format(command, sender))
			if command == "reload-legislation":
				self.logger.info("Reloading legislation.")
				importlib.reload(legislation)
				self.legislator = legislation.Legislation(self.file_log_handler, self.stream_log_handler, self.channel)
			else:
				self.logger.warning("Command \"{}\" unknown.".format(command))
			
	def on_dccmsg(self, c, event):
		self.logger.error("on_dccmsg called but not implemented!")

	def on_dccchat(self, c, event):
		self.logger.error("on_dccchat called but not implemented!")

	def on_action(self, c, event):
		message = event.arguments[0]
		message = "* {} {}".format(event.source.split("!")[0], message)

		self.add_to_backlog(message)

	def on_join(self, c, event):
		nick = event.source.split("!")[0]
		message = "*** Joins: {}".format(nick)

		self.add_to_backlog(message)

	def on_part(self, c, event):
		nick = event.source.split("!")[0]
		try:
			part_message = event.arguments[0]
		except IndexError:
			# A debug message is probably not needed here.
			# Parts without a message are not uncommon.
			part_message = ""
		message = "*** Parts: {} ({})".format(nick, part_message)

		self.add_to_backlog(message)

	def on_quit(self, c, event):
		nick = event.source.split("!")[0]
		try:
			quit_message = event.arguments[0]
		except IndexError:
			quit_message = ""
		message = "*** Quits: {} ({})".format(nick, quit_message)
		
		self.add_to_backlog(message)

	def on_kick(self, c, event):
		kicker_nick = event.source.split("!")[0]
		kickee_nick = event.arguments[0]
		kick_message = event.arguments[1]
		message = "*** Kick: {} by {} ({})".format(kickee_nick, kicker_nick, kick_message)

		self.add_to_backlog(message)

	def on_mode(self, c, event):
		changer_nick = event.source.split("!")[0]
		mode_change = event.arguments[0]
		try:
			changee_nick = event.arguments[1]
		except IndexError:
			# This is normal if channel modes are changed,
			# len(event.arguments) is 1, so there is no event.arguments[1].
			# The target is the channel, so set changee_nick to the current channel (event.target)
			changee_nick = event.target

		message = "*** Mode: {} {} by {}".format(mode_change, changee_nick, changer_nick)

		self.add_to_backlog(message)

	def on_topic(self, c, event):
		changer_nick = event.source.split("!")[0]
		new_topic = event.arguments[0]
		message = "*** Topic: \"{}\" by {}".format(new_topic, changer_nick)

		self.add_to_backlog(message)

	def on_pubnotice(self, c, event):
		sender_nick = event.source.split("!")[0]
		notice_message = event.arguments[0]
		message = "*** Notice: {} \"{}\" by {}".format(event.target, notice_message, sender_nick)

		self.add_to_backlog(message)

	def get_version(self):
		return self.pretty_version

	def message_to_backlog_item(self, message, timestamp):
		return BacklogItem(message, timestamp)

	def reply(self, sender_nick, reply):
		c = self.connection
		c.privmsg(self.channel, "{}: {}".format(sender_nick, reply))

	def add_to_backlog(self, message, timestamp=None):
		if timestamp == None:
			timestamp = datetime.datetime.utcnow().time()

		if isinstance(message, str):
			message = self.message_to_backlog_item(message, timestamp)

		if len(self.backlog) > self.max_backlog_length:
			self.backlog.pop(0) # Remove the first item from the backlog.
			self.logger.debug("Backlog too long. Popped first line.")

			# This also means that the active proposal has to be shifted by - 1
			if self.legislator.active_proposal != None:
				self.legislator.active_proposal -= 1
				if self.legislator.active_proposal <= -1:
					self.legislator.active_proposal = None
					self.logger.debug("Active proposal <= -1. Active proposal is now out of backlog range. Setting to None.")

		# Note that we do not need to truncate the timestamp - BacklogItem's constructor does so automatically.
		self.backlog.append(message)
		self.logger.debug("Appended new backlog message \"{}\"".format(message.message))

		# Add to the channel logs, too.
		self.channel_logger.append("{} {}".format(message.timestamp, message.message))

	def shutdown_handler(self, signum, frame):
		""" Called when a SIGTERM, or SIGINT event is handled.
			Just calls "shutdown" in turn, which performs all cleanup.
		"""
		self.logger.info("SIGTERM or SIGINT caught. (signum {})".format(signum))
		self.shutdown()

	def shutdown(self):
		self.channel_logger.append_log_end_message()
		self.logger.info("Shutting down.")
		sys.exit(0)
		
