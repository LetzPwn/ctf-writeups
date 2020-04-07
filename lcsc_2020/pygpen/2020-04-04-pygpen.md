---
layout:         writeup
title:          "Pyg-Pen"
date:           2020-04-04 12:00:00 +0200
event:          "LCSC CTF 2020"
categories:     [writeup]
ctf_categories: [misc]
author:         "Nanohenry (aka neo)"
---
# Pyg-Pen

## TL;DR

Use the exit code from Python's `os.system()` to send a file byte-by-byte back
to the user.

(**note:** not the most efficient solution)

## Given information

Instructions to `nc` to a port on a URL.

## Solution

Netcatting into the port gives a prompt. After some experiementation, I
discovered it to be a Python interpreter, which made sense considering the name
of the challenge.

After some more looking around, running `globals()` showed that there were
"unsafe builtins", like `__import__` or `input()`. The function also showed a
few modules, including `SocketServer`.

My first idea to solving it was to simply open and read the flag file, but
anything that included the word "open" in it failed instantly and just returned
the word "no". I also couldn't import any modules because of the "unsafe
builtins" thing I mentioned.

After looking around even more, I found that the `SocketServer` has an
interesting member, `os` (which is Python's `os` module). Running
`SocketServer.os.lisdir(".")` showed that there was a file called `flag.txt`.
So, target found.

Going through the `os` module, there wasn't much that was useful, except for
`os.system()`, which allowed me to run arbitrary commands. Unfortunately, I
quickly discovered that `cat flag.txt` wouldn't work, for two reasons: because
the interpteter didn't like spaces and because `os.system()` only returns the
exit code and no output. While the former could be fixed by replacing spaces
with `\x20` (hex 20 is the ASCII code for space), the latter was an actual
problem.

Saying "only returns the exit code" is a bit badly put, since it does at
least return *something*. Many commands that I ran with `os.system()` returned
exit code 0, but others didn't. That sparked an idea: I could send at least one
byte of data from a script on the server back to me via the exit code. Of
course, it would require importing  `sys` for `sys.exit()`, but since it was
running in its own process, the import restrictions didn't apply anymore.

I tested it with the command `python3 -c "import sys\nsys.exit(3)"` (of course
spaces replaced with `\x20`) and it returned `768`. What's that, you migth
wonder? Well, it's the exit code bit-shifted left by 8 places (`3 >> 8 = 768`).
So I knew the idea would work.

It didn't take me long to write a script that would craft a Python command to
return each of the first 64 chraracters of the flag:

```python
from pwn import *

l = r"SocketServer.os.system('python3\x20-c\x20\"import\x20sys\nf=\x6Fpen(\'flag.txt\',\'rb\').read()\nsys.exit(f[{}])\"')"

conn = remote("[REDACTED]", 50032)
for i in range(64):
	conn.recvuntil("> ")
	conn.sendline(l.format(i))
	d = conn.readline().decode("utf-8")
	print(chr(int(d.split(" ")[-1].strip()) >> 8), end = "")
conn.close()
```

Running the script slowly but steadily printed out the flag characters.

I know there might be easier ways (such as a convenient one-liner \*cough
cough\*), but this was way more fun.
