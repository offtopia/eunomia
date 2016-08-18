import irc.bot
import irc.strings
import logging
import legislation
import datetime
import eunomialog
from backlog import BacklogItem

class EunomiaBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, ident_packed=None, port=6667):
		self.logger = logging.getLogger("EunomiaBot")
		self.logger.setLevel(logging.INFO)

		lformat = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)-5.5s]: %(message)s", "%Y-%m-%d %H:%M:%S")

		fh = logging.FileHandler("eunomia.log")
		fh.setFormatter(lformat)
		sh = logging.StreamHandler()
		sh.setFormatter(lformat)

		self.logger.addHandler(fh)
		self.logger.addHandler(sh)

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

	def on_nicknameinuse(self, c, event):
		c.nick(c.get_nickname() + "_")
		self.logger.info("Nickname {} was in use. Trying {}.".format(c.get_nickname(), c.get_nickname() + "_"))

	def on_welcome(self, c, event):
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
		message = "<{}> {}".format(event.source.split("!")[0], message)

		timestamp = datetime.datetime.utcnow().time()

		mbi = self.message_to_backlog_item(message, timestamp)

		self.add_to_backlog(mbi, timestamp)

		self.legislator.dereference_if_vote(mbi, self.backlog)

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
		part_message = event.arguments[0]
		message = "*** Parts: {} ({})".format(nick, part_message)

		self.add_to_backlog(message)

	def on_quit(self, c, event):
		nick = event.source.split("!")[0]
		quit_message = event.arguments[0]
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
		changee_nick = event.arguments[1]
		mode_change = event.arguments[0]
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
