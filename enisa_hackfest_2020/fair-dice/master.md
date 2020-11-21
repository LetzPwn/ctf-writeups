---
layout: writeup
categories: [writeup]
title:  "fair-dice"
author: "Luxy"
date:   2020-11-16 23:45:00 CET
event: "ENISA HACKFEST 2020"
ctf_categories: [Misc, Programming]
image: ""
---

## Description

> Are you willing to throw dices and try your luck at DCTF?

> Flag format: DCTF{sha256}

> ### About the challenge
> The challenge was initially published at DefCamp Capture the Flag 2019 - final phase. The challenge was created by [Bit Sentinel](https://bit-sentinel.com), a top-notch team of specialists in cyber security.

> DefCamp Capture The Flag [( D-CTF )](https://dctf.def.camp) is the most shattering and rebellious security CTF competition in the Central Eastern Europe. The competition was launched by Cyber Security Research Center from Romania in 2011 as part of DefCamp, one of the largest cyber security & hacking conference from CEE.

## TL: DR

A bot challenges you to a game of dice. You have to win 4 sets in a row to get the flag (1 set consists of 101 dice throws). Each set the rules change.

## Complete Writeup

``` 
[x] Opening connection to 35.242.192.203 on port 30328
[x] Opening connection to 35.242.192.203 on port 30328: Trying 35.242.192.203
[+] Opening connection to 35.242.192.203 on port 30328: Done
[*] Switching to interactive mode
Welcome to a fair dice game.
 - We are going to play some fair rounds. Let's say 101.
 - We both throw one dice. The biggest numbered showed on the dice, wins!
 - The person who wins more rounds from 101, wins that game.
 - If you win too many games in the same session, I am going to alter the game rules to make it fairer for me.
 - If you are going to win four games, I will give you a special code.
 - Note that I am getting bored very fast and I will close this game soon.
Should we start?
```

### Getting to know the game structure

The first thing I had to do was get to know how exactly the bot was giving order and commands. Once I found out what he wants for the first set, I could write a script for it and move on.

### Set 1

``` 
Here is the blue dice:

       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  3  xx  6  xx  3  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
Ok?
Here is the yellow dice:

       xxxxxxx
       x     x
       x  5  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx   
x     xx     xx     x
x  5  xx  5  xx  2  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  2  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  2  x
       x     x
       xxxxxxx
Ok?
Here is the red dice:

       xxxxxxx
       x     x
       x  4  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  4  xx  1  xx  4  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  4  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  4  x
       x     x
       xxxxxxx
Ok?
```

In the first set, the bot presents you 3 dice (blue, yellow, red) and he starts by picking one. You then have to choose one of the 2 remaining ones. 

``` 
What are you choosing? blue / yellow / red: red
Hey that is my dice!!!! Take another one!

or

What are you choosing? blue / yellow / red: purple
I do not know that color...
```

If you choose the same dice as the bot or a color he doesn't know, he'll complain and you have to choose again.

``` 
I am chosing the yellow dice!
What are you choosing? blue / yellow / red:
```

The dice are rolled and whoever gets a higher number, wins the round. 

``` 
You won with 55 rounds!

Time for second game!
```

If you have more points after 101 rounds than the bot, you win the first set.

### Set 2

``` 
You are two lucky, altering rules!
 - We are playing with the same dices.
 - Each one of us selects 1 color of the playing dice.
 - Each one of us throws 2 times the playing dice and add the numbers together.
 - The biggest number wins.
 ```

In the second set, the rules change a bit. The bots uses the same 3 dice, but this time they are always rolled twice. (e.g., the bot chooses red, so he rolls red twice, after every roll, a winner is defined, but for the second roll, both rolls are added. So if the bot rolls 3 as a first roll and you 1, then the bot wins the first round. But if you roll a 5 in the second round and the bot a 2, you win with 1+5=6 points against 3+2=5)

``` 
You won with 54 rounds!

Time for third game!
```

If you win more often than the bot in 101 rounds, you move on to set 3.

### Set 3

``` 
OMG! Again you? You are two lucky, altering rules!
 - We are playing 4 new dices.
 - Same rules as 1st game...
 - You shall not pass!
 ```

In the third round, the bot adds a fourth die (green) and also changes the other colored dice. 

``` 
Let me show you the 4 dices we are going to play:

Here is the blue dice:

       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  3  xx  3  xx  3  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  3  x
       x     x
       xxxxxxx
Ok?

Here is the yellow dice:

       xxxxxxx
       x     x
       x  6  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  6  xx  2  xx  2  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  2  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  2  x
       x     x
       xxxxxxx
Ok?

Here is the red dice:

       xxxxxxx
       x     x
       x  5  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  5  xx  5  xx  1  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  1  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  1  x
       x     x
       xxxxxxx
Ok?

Here is the green dice:

       xxxxxxx
       x     x
       x  0  x
       x     x
       xxxxxxx
xxxxxxxxxxxxxxxxxxxxx
x     xx     xx     x
x  0  xx  4  xx  4  x
x     xx     xx     x
xxxxxxxxxxxxxxxxxxxxx
       xxxxxxx
       x     x
       x  4  x
       x     x
       xxxxxxx
       xxxxxxx
       x     x
       x  4  x
       x     x
       xxxxxxx
Ok?
```

The rules are the same as in the first set: 1 throw and the highest number wins. The player with the most wins after 101 rounds wins the set.

``` 
You won with 52 rounds!

Time for fourth game!  
```

### Set 4

``` 
... No words ...  You are two lucky, altering rules!
 - We are playing 4 new dices.
 - Same rules as 2nd game...
 - If you beat me one more time, I am going to give you my flag!
 ```

The fourth and final set is played with 4 dice again but this time the rules are the same in round 2. In the first round the highest roll wins and in the next round the highest sum of the 2 rolls wins. If you win more often than the bot in 101 rounds, you win the set and he presents you the flag of the challenge.

``` 
You won with 67 rounds!
DCTF{7537c933a266a45500c5bd35f20679539f596df9e706dc95fae22d15b812141f}
Good luck.
```

### Some remarks

I chose the colors based on what I felt was a better choice. Sometimes I lose a round and sometimes I win it with the same choices. There may be some math behind it, so that you can find out which die to choose to have the highest chance of winning, but I did not figure that out completely. So I changed my script to keep restarting if I lose. This way I could find the flag without finding the math behind the whole thing and just hoping the luck is on my side.

## Final Solution

``` Python
from pwn import remote

def beginGame(won):
	p = remote("35.242.192.203",30328)
	p.sendline()
	for i in range(3):
		p.recvuntil("dice")
		p.sendline()
	my_score = 0
	your_score = 0
	round = 1
	print("STARTING ROUND", round)

	while(round < 5):
		
		p.recvuntil("I am chosing the ")
		color = p.recvuntil("dice").split()[0].decode()
		#print(color)
		if (round == 1):
			if color == "red":
				p.sendline("yellow")
			else:
				p.sendline("red")
		elif (round == 2 or round == 4):
			if color == "red":
				p.sendline("blue")
			else:
				p.sendline("red")

		elif (round == 3):
			if color == "green":
				p.sendline("yellow")
			else:
				p.sendline("green")
		p.recvuntil("Your number")
		score = p.recvuntil("win").split()[-2].decode()
		if(score == "You"):
			my_score += 1
		else:
			your_score += 1
		#print("Score: Player:",my_score,"vs Comp: ",your_score)
		if my_score + your_score == 101:
			if my_score < your_score:
				print("MISSION FAILED, WE'LL GET 'EM NEXT TIME")
				print("TRYING AGAIN")
				return False
			else:
				my_score = 0
				your_score = 0
				round += 1
				if (round == 5):
					p.recvuntil("rounds!")
					flag = p.recvuntil("}").decode()
					print(flag)
					return True
				print("STARTING ROUND", round)
				if (round == 3):
					for i in range(4):
						p.sendline()

won = False
while not won:
	won = beginGame(won)
```
