from collections import defaultdict
import random

markov = defaultdict(list)
STOP_WORD = "\n"

def add_to_brain(msg, chain_length, write_to_file=False):
	if write_to_file:
		f = open("training_text.txt", "a")
		f.write(msg+'\n')
		f.close()
	
	buf = [STOP_WORD]*chain_length
	for word in msg.split():
		markov[tuple(buf)].append(word.upper())
		del buf[0]
		buf.append(word)
	markov[tuple(buf)].append(STOP_WORD)


def generate_sentence(msg, chain_length, max_words=10000):
	buf = msg.strip().upper().split()[:chain_length]
	message = buf[:]
	if len(msg.split()) < chain_length:
		for i in xrange(len(msg), chain_length):
			message.append(random.choice(markov[random.choice(markov.keys())]).upper())
	for i in xrange(max_words):
		try:
			next_word = random.choice(markov[tuple(buf)]).upper()
		except IndexError:
			continue
		if next_word == STOP_WORD:
			break
		message.append(next_word)
		del buf[0]
		buf.append(next_word)
	message = " ".join(message)
	if len(message.split()) < chain_length:
		return generate_sentence("", chain_length, max_words)
	else:
		return message

def populateBrain(filename, chain_length):
	f = open(filename, 'r')
	for line in f:
		add_to_brain(line, chain_length, True)
	f.close()