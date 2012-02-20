from twisted.words.protocols import irc
from twisted.internet import protocol

import brain

import ConfigParser
import twitter
import sys
import os
import random
import re
import Image, ImageDraw, ImageFont
import textwrap
import pycurl
import json
import cStringIO
from twisted.internet import reactor

class twistedBot(irc.IRCClient):
    def __init__(self):
        lastMsg = ""

    def _get_nickname(self):
    	return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
    	self.join(self.factory.channel)
    	print "Signed on as "+self.nickname

    def joined(self, channel):
    	print "Joined "+channel

    def privmsg(self, user, channel, msg):
        #print ("%s %s %s")%(user, channel, msg)
        if "loudbot" in user:
            return
    	if not user:
    		return
        
        newmsg = ""
        prefix = ""
    	if self.nickname in msg:
            msg = re.compile(self.nickname+"[:,]* ?", re.I).sub("", msg)
            prefix = "%s: "%(user.split('!', 1)[0],)
            extras = self.parseMsg(msg)
            if extras == "": 
                newmsg = self.getsentence(msg)
            else:
                newmsg = extras
        elif "<3" in msg:
            msg = re.compile("<3"+"[:,]* ?", re.I).sub("", msg)
            prefix = "%s: "%(user.split('!', 1)[0],)
            extras = self.parseMsg(msg)
            if extras == "":
                newmsg = self.getsentence(msg)
            else:
                newmsg = extras
    	elif channel == self.nickname:
            extras = self.parseMsg(msg)
            if extras == "":
                newmsg = self.getsentence(msg)
            else:
                newmsg = extras
        elif random.random() <= self.factory.chattiness:
            msg = re.compile(user.split('!',1)[0]+"[:,]* ?", re.I).sub("", msg)
            newmsg = self.getsentence(msg)
        
        self.lastMsg = newmsg
        
        if channel == self.nickname:
            self.msg(user.split('!', 1)[0], prefix+newmsg)
        elif newmsg != "":
            self.msg(self.factory.channel, prefix+newmsg)

    def parseMsg(self, msg):
        base = "http://twitter.com/anglebracket3/status/"
        if "twitlast" in msg:
            if hasattr(self, 'lastMsg') and self.lastMsg != "":
                print self.lastMsg
                status = self.factory.api.PostUpdate(self.lastMsg)
            else:
                return ""
            return base + str(status.id)
        elif "kittify" in msg:
            return self.kittify()
        elif "kitlast" in msg:
            url = self.kittify()
            status = self.factory.api.PostUpdate(url)
            return base+str(status.id)+" "+url
        elif "source" in msg:
            return "https://github.com/clholgat/twistedBot"
        elif "help" in msg or "wat" in msg:
            return "Commands: twitlast - tweets the last message; source - link to bot's source; kittify - kittenify the last message; kitlast - kittenify and post image to twitter; help - this message"
        else:
            return ""

    def kittify(self):
        if not hasattr(self, 'lastMsg') or self.lastMsg == "":
            return ""
        print self.lastMsg
        kitten = "kitten%d.jpg"%random.choice(range(1,10))
        im = Image.open("kittens/"+kitten)
        box = im.getbbox()
        width = box[2]
        height = box[3]
        fsize = 70
        lines = textwrap.wrap(self.lastMsg, int(width/fsize*1.65))
        while len(lines) > 2:
            fsize -= 2
            lines = textwrap.wrap(self.lastMsg, int(width/fsize*1.65))

        draw = ImageDraw.Draw(im)
        font = ImageFont.truetype("/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-B.ttf", fsize)
        #font = ImageFont.truetype("Ubuntu.ttf", fsize)
        draw.text((10, 10), lines[0], font=font, fill="white")
        if len(lines) > 1:
            draw.text((10, height-10-fsize), lines[-1], font=font)
        im.save("tmp.jpg")

        response = cStringIO.StringIO()

        c = pycurl.Curl()
        values = [
            ("key", "8d4b1396c3d2a3712b299594600e0068"),
            ("image", (c.FORM_FILE, "tmp.jpg"))
        ]
        c.setopt(c.URL, "http://api.imgur.com/2/upload.json")
        c.setopt(c.HTTPPOST, values)
        c.setopt(c.WRITEFUNCTION, response.write)
        c.perform()
        c.close()
        ret = json.loads(response.getvalue())
        return str(ret['upload']['links']['original'])

    	
    def getsentence(self, msg):
        brain.add_to_brain(msg, self.factory.chain_length, write_to_file=True)
        sentence = brain.generate_sentence(msg, self.factory.chain_length, self.factory.max_words)
        if sentence:
            return sentence
        else:
            return msg


class twistedBotFactory(protocol.ClientFactory):
    protocol = twistedBot

    def __init__(self, channel, nickname="testthathree", chain_length=3, chattiness=1.0, max_words=10000):
        config = ConfigParser.ConfigParser()
        config.read("twitter.config")
        self.channel = channel
        self.nickname = nickname
        self.chain_length = chain_length
        self.chattiness = chattiness
        self.max_words = max_words
        self.api = twitter.Api(config.get('OAuth','consumer_key'), config.get('OAuth','consumer_secret'), config.get('OAuth','access_token_key'), config.get('OAuth', 'access_token_secret'))
	
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
            brain.add_to_brain(line.upper(), chain_length)
        print "brain loaded"
        f.close()
    reactor.connectTCP("irc.freenode.net", 6667, twistedBotFactory("#"+chan, 'lessthanthree', 2, chattiness=0.05))
    reactor.run()
