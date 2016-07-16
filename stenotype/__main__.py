import bot

def main(args=None):
	server = "irc.freenode.net"
	channel = "##ingsoc"
	nick = "stenotype"

	bot_inst = bot.StenoBot(channel, nick, server)
	bot_inst.start()

if __name__ == "__main__":
	main()	
