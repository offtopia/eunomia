import irc.bot
import irc.strings
import logging

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
		a = event.arguments[0].split(":", 1)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			self.do_command(event, a[1].strip())
	
	def on_dccmsg(self, c, event):
		self.logger.error("on_dccmsg called but not implemented!")

	def on_dccchat(self, c, event):
		self.logger.error("on_dccchat called but not implemented!")
	
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
