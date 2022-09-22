---
layout: writeup
categories: [writeup]

# Mandatory parameters
title:  "Healthcheck 1"
author: "Jaak"
date:   2022-09-03 01:10:05 +0200
event: "Balsn CTF 2022"

# Optional parameters
ctf_categories: [web]
image: "img/balsnctf_challenges.png"
---

# Health Check 1

## Description

Want to know whether the challenge is down or it's just your network down? Want to know who to send a message when you want to contact an admin of some challenges? Take a look at our "fastest" Health Check API in the world!

http://fastest-healthcheck.balsnctf.com

Warning: Do not violate our CTF rules.

Author: chiffoncake

## Solution

Under the provided link, we just see a hello world message in json.
Gobuster finds a `/docs` endpoint. Navigating to it reveals documentation about more endpoints:
![](https://hedgedoc.pwned.lu/uploads/5c8e9fe6-3229-4afc-ae47-dd7797f38bb2.png)

![](https://hedgedoc.pwned.lu/uploads/3f4ef5d1-1414-4415-83f0-3f5312e688f1.png)

So it seems we found a way to upload a zipfile containing a `run` executable. There is a process that executes it in a 30 second interval. The executable is expected to create a `status.json` file, where `run` is expected to store some results in. When uploading zip file, we receive the name it is stored under. Using the second endpoint, we can request the respective json of the commands we run from the uploaded zip. 

So seems like we got command execution and a way of checking what our commands do. Let's try it.

I am creating a shell script containing the command i want to run:

```sh
#!/bin/sh

touch ./status.json

pwd > ./status.json

```

![](https://hedgedoc.pwned.lu/uploads/7835c431-d4e3-4eac-9e73-11ca03ff0e82.png)

- Listing files in interesting directory with `ls ../..` (note that flag1.py is interesting for us; flag2 is for a different challenge):

![](https://hedgedoc.pwned.lu/uploads/01a4938c-29ea-4067-aa0c-b1bd06c8bdb5.png)

- Taking a look at permissions with `ls -la ../..`. Looks like we do not have read permission to the `flag1.py` script.

![](https://hedgedoc.pwned.lu/uploads/ab14b439-b928-437e-9053-57267b1e687c.png)

- Since it is a script and theres a `__pycache__` folder, maybe we can read the compiled version of the script instead of the script itself. Let's see what's in there with `ls ../../__pycache__`:

![](https://hedgedoc.pwned.lu/uploads/bc847a58-2ef1-4fd4-a942-01f9f1e7a6c8.png)

Finally, at 3:30 in the morning, 27 minutes before the CTF ended, I managed to get the flag with `xxd ../../__pycache__/flag1.cpython-310.pyc`:

![](https://hedgedoc.pwned.lu/uploads/9f2eb19e-6fb1-4521-a811-e89cf7176e17.png)

`BALSN{y37_4n0th3r_pYC4ch3_cHa1leN93???}`

## Reverse shell solution

I did not get a reverse shell solution working during the CTF unfortunately. The way I did it was very laborious, crafting each zip file seperately, uploading it and waiting for execution. Also for commands that resulted in an error, I did not get a result in the status.json at all, making my solution very tedious.

A reverse shell would have been the much better way. Some people on the BALSNCTF discord shared their solution. Here is a code snippet from a C script. When compiled as `run` and uploaded inside a zip, a reverse shell should be obtained. I tried it today where CTF is over, but I think they disabled the processes running the executables already.