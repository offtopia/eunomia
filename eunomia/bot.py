import irc.bot
import irc.strings

class EunomiaBot(irc.bot.SingleServerIRCBot):
	def __init__(self, channel, nickname, server, port=6667):
		irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		self.channel = channel

		self.reloading = False
	
	def on_nicknameinuse(self, c, event):
		c.nick(c.get_nickname() + "_")
	
	def on_welcome(self, c, event):
		c.join(self.channel)
	
	def on_privmsg(self, c, event):
		self.do_command(event, event.arguments[0])

	def on_pubmsg(self, c, event):
		a = event.arguments[0].split(":", 1)
		if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
			self.do_command(event, a[1].strip())
	
	def on_dccmsg(self, c, event):
		print("[DEBUG]: on_dccmsg not implemented.")
	
	def on_dccchat(self, c, event):
		print("[DEBUG]: on_dccchat not implemented.")
	
	def do_command(self, event, command):
		sender_nick = event.source.nick
		c = self.connection

		if command == "disconnect":
			self.disconnect()

		elif command == "die":
			self.die("The life of the dead is placed in the memory of the living.")

		elif command == "ping":
			c.privmsg(self.channel, "{}: pong".format(sender_nick))

		else:
			c.notice(sender_nick, "Unknown command: " + command)
