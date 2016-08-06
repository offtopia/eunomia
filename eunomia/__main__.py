import bot
import configparser
import sys

def main(args=None):
	config_name = "eunomia.ini"

	config = configparser.ConfigParser()
	config.read(config_name)

	if config.sections() == []:
		# If the config sections are empty, then an error has occurred in reading the config.
		# Either it is empty or the file does not exist.

		# This exception should never be caught, so we don't need to sys.exit()
		raise Exception("Config file \"{}\" not found or empty! Aborting.".format(config_name))

	irc_config = config["irc"]
	ident_config = config["ident"]

	server = irc_config.get("server", "irc.freenode.net")
	channel = irc_config.get("channel", "#eunomia_default")
	nick = irc_config.get("nick", "eunomia")
	port = irc_config.getint("port", 6667)

	ident_username = ident_config.get("username", nick)
	ident_pass = ident_config.get("password", "eunomia_default")
	ident_method = ident_config.get("method", "none")

	ident_packed = (ident_username, ident_pass, ident_method)

	if ident_method == "none":
		ident_packed = None

	bot_inst = bot.EunomiaBot(channel, nick, server, ident_packed, port)
	bot_inst.connection.buffer_class.errors = "replace"
	bot_inst.start()

if __name__ == "__main__":
	main()
