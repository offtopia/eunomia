import bot

def main(args=None):
	server = "irc.freenode.net"
	channel = "##ingsoc"
	nick = "eunomia"

	bot_inst = bot.EunomiaBot(channel, nick, server)
	bot_inst.start()

if __name__ == "__main__":
	main()	
