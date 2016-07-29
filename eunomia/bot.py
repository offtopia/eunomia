import irc.bot
import irc.strings
import logging
import legislation
import datetime

class EunomiaBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		self.logger = logging.getLogger("EunomiaBot")
		self.logger.setLevel(logging.INFO)

		lformat = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)-5.5s]: %(message)s")

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

		self.legislator = legislation.Legislation(fh, sh)

		self.max_backlog_length = 50
		self.backlog = []

	def on_nicknameinuse(self, c, event):
		c.nick(c.get_nickname() + "_")
		self.logger.info("Nickname {} was in use. Trying {}.".format(c.get_nickname(), c.get_nickname() + "_"))

	def on_welcome(self, c, event):
		c.join(self.channel)
		self.logger.info("Connection complete.")

	def on_privmsg(self, c, event):
		self.do_command(event, event.arguments[0])
		self.logger.info("Got a PRIVMSG: \"{}\"").format(event.arguments[0])

	def on_pubmsg(self, c, event):
		message = event.arguments[0]
		message = "<{}> {}".format(event.source.split("!")[0], message)

		self.add_to_backlog(message, datetime.datetime.now().time())

		a = event.arguments[0].split(":", 1)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			self.do_command(event, a[1].strip())

		self.legislator.dereference_if_vote((message,datetime.time()), self.backlog, self.backlog)

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

	def do_command(self, event, command):
		sender_nick = event.source.nick
		c = self.connection

		self.logger.info("Nick \"{}\" attempts to perform \"{}\" command.".format(sender_nick, command))

		if command == "disconnect":
			self.disconnect()

		elif command == "die":
			self.die("The life of the dead is placed in the memory of the living.")

		elif command == "ping":
			self.reply(sender_nick, "pong")

		else:
			self.reply(sender_nick, "Unknown command.")
			self.logger.warning("Unknown command \"{}\"".format(command))

	def reply(self, sender_nick, reply):
		c = self.connection
		c.privmsg(self.channel, "{}: {}".format(sender_nick, reply))

	def add_to_backlog(self, message, timestamp=datetime.datetime.now().time()):
		if len(self.backlog) > self.max_backlog_length:
			self.backlog.pop(0) # Remove the first item from the backlog.
			self.logger.debug("Backlog too long. Popped first line.")

			# This also means that the active proposal has to be shifted by - 1
			if self.legislator.active_proposal != None:
				self.legislator.active_proposal -= 1
				if self.legislator.active_proposal <= -1:
					self.legislator.active_proposal = None
					self.logger.debug("Active proposal <= -1. Active proposal is now out of backlog range. Setting to None.")

		# datetime.now().time() also gives milliseconds. Ignore milliseconds.
		timestamp_trunc = datetime.time(timestamp.hour, timestamp.minute, timestamp.second)

		self.backlog.append((message, timestamp_trunc))
		self.logger.debug("Appended new backlog message \"{}\"".format(message))
