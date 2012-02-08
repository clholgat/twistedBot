from twisted.words.protocols import irc
from twisted.internet import protocol

import brain

import sys
import os
import random
import re
from twisted.internet import reactor

class twistedBot(irc.IRCClient):
    def _get_nickname(self):
    	return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
    	self.join(self.factory.channel)
    	print "Signed on as "+self.nickname

    def joined(self, channel):
    	print "Joined "+channel

    def privmsg(self, user, chanel, msg):
        if "loudbot" in user:
            return
    	if not user:
    		return
    	if self.nickname in msg:
    		msg = re.compile(self.nickname+"[:,]* ?", re.I).sub("", msg)
    		prefix = "%s: "%(user.split('!', 1)[0],)
        elif "<3" in msg:
            msg = re.compile("<3"+"[:,]* ?", re.I).sub("", msg)
            prefix = "%s: "%(user.split('!', 1)[0],)
    	else:
    		prefix = ""
    	brain.add_to_brain(msg, self.factory.chain_length, write_to_file=True)
    	if prefix or random.random() <= self.factory.chattiness:
    		sentence = brain.generate_sentence(msg, self.factory.chain_length, self.factory.max_words)
    		if sentence:
    			self.msg(self.factory.channel, prefix+sentence)

class twistedBotFactory(protocol.ClientFactory):
	protocol = twistedBot

	def __init__(self, channel, nickname="lessthathree", chain_length=3, chattiness=1.0, max_words=10000):
		self.channel = channel
		self.nickname = nickname
		self.chain_length = chain_length	
		self.chattiness = chattiness
		self.max_words = max_words
	
	def clientConnectionLost(self, connector, reason):
		print "Lost connection "+str(reason)+", reconnection"
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "Could not connect: "+str(reason)

if __name__ == "__main__":
    chan = ""
    chain_length = 2
    try:
	   chan = sys.argv[1]
    except IndexError:
        print "You need a channel name"
    if os.path.exists('training_text.txt'):
        f = open('training_text.txt', 'r')
        for line in f:
            brain.add_to_brain(line, chain_length)
        print "brain loaded"
        f.close()
    reactor.connectTCP("irc.freenode.net", 6667, twistedBotFactory("#"+chan, 'lessthanthree', 2, chattiness=0.05))
    reactor.run()