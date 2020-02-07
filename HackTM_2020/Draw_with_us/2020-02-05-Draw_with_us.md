---
layout: writeup
title:  "Draw with us"
source: "http://167.172.165.153:60000/"
solves: "85/1528"
date:   2020-02-05 17:10:05 +0200
event: "HackTM CTF 2020"
categories: [writeup]
ctf_categories: [web, node.js, javascript]
image: "website.png"
author: "Alain K."
---

## Description
> Come draw with us!  
> [http://167.172.165.153:60000/](http://167.172.165.153:60000/),  
> Author: stackola.  
> Hint! Changing your color is the first step towards happiness.  
> [Source code](stripped.js). 

![Image of Website](website.png)

## TL;DR
The challenge consisted of of 3 bypasses to get a signed JWT token with admin rights.
1. Bypass `isAdmin() ` check with Unicode case folding. `username.toLowerCase() == adminUsername.toLowerCase()`
2. Get blacklisted server info by bypassing the blacklist check. 
`let blacklist = ["p", "n", "port"]; if(!blacklist.includes(userRequest)) return rights[userRequest];` can be bypassed by setting userRequest to an array: `["n"]`, which will result in `rights[["n"]]`, which is the same as `rights["n"]` for javascript.
3. Use the server info to get a new signed JWT token with the same id as admin: 0. 
4. Request flag with signed admin JWT token

## Complete Writeup
The website consisted of a pixel board where users could draw on after registering with a username. The color was randomly assigned to the user: either black or white. Looking at the board however, one could see that some users managed to draw with other colors already. Given the hint in the desciption, this seemed to be the first problem to solve. As the source code got provided to us, let's take a closer look into the part where the color can be changed:
```javascript
app.post("/updateUser", (req, res) => {
  let uid = req.user.id;
  let user = users[uid];
  if (!user || !isAdmin(user)) {
    res.json(err("You're not an admin!"));
    return;
  }
  users[uid].color = parseInt(req.body.color);
});
```
An intersting thing to notice is that requests are treated as JSON objects. An example POST request body to change the color could look like the follwing:
`{color: 0xDEDBEE}`.
However, there is a protection mechanism set in place that only allows admins to change the color. So let's take a closer look into what the `isAdmin() ` function does:
```javascript
function isAdmin(u) {
  return u.username.toLowerCase() == config.adminUsername.toLowerCase();
}
```
As we know the name of the admin ("hacktm"), the first try was to register as a user with the same name as the admin. However this fails due to the following validation function:
```javascript
function isValidUser(u) {
  return (
    u.username.length >= 3 &&
    u.username.toUpperCase() !== config.adminUsername.toUpperCase()
  );
}
```
There are two things that my eyes caught on:
1. `isValidUser()` uses a strict equality check (`!==`), whereas `isAdmin()` uses the non-strict equality check (`==`)
2. `isValidUser()` uses `toUpperCase()` for comparing, `isAdmin()` uses `toLowerCase()`

The 2nd point reminded me of UTF case folding attacks. So I checked some special case folding scenarios on the [UTF-8 website](https://unicode.org/faq/casemap_charprop.html) and tried them to force the `toLowerCase` to result into the "hacktm" string, whereas the `toUpperCase` NOT transforming to "HACKTM". I tried some greek and turkish characters and some other special characters. Even though the results "looked" correct, they were not the thing I needed in Upper- or lower case (Example good candidate: HaϹkTM.toUpperCase() = "HAϹKTM" which is not the same as "HACKTM", as the "Ϲ" is not a standard ascii "C" but a greek UTF-8 character. HaϹkTM.toLowerCase() = "haϲktm", however the isAdmin() check would not pass as the transformed little "ϲ" is also a special greek character). 

After a lot of unsuccesful tries, I gave up with the unicode bypass and spent some time to abuse the non-strict eqauality check. 
As we can pass any valid JSON, I tried the following as username:
```javascript
{
  username: ["hack","t","m"]
}
```

this failed because toLowerCase() and toUpperCase() are not defined on arrays. But otherwise it would have worked as `username.length >= 3` and because of the non-strict equality check `["hack","t","m"] == "hacktm"` would have resulted in true. Another idea was to use an object as username:

```javascript
{
  username: {"toUpperCase":"hacktm", "toLowerCase": "hacktm"}
}
```

But this clearly fails because toUpperCase/toLowerCase are not callable functions.

I gave up with both approaches and concluded that if there is a possible bypass, it is more probable to be an UTF case folding bypass.

So I looked at the rest of the code and tried to make sense of it. The application uses JWT for authentication. It stores the userId in it, and we know that the `userId = 0` is the administrator account. Seeing JWT tokens in CTF challenges, it is always a good idea to try to bypass the signing by setting the signing algorithm to none. However this did not work and also looking at the source code, one can see it uses a state of the art library with no current possible vulnerabilites.


Next step was to look into a strange `init` function: 
```javascript
app.post("/init", (req, res) => {

  let { p = "0", q = "0", clearPIN } = req.body;

  let target = md5(config.n.toString());

  let pwHash = md5(
    bigInt(String(p))
      .multiply(String(q))
      .toString()
  );

  if (pwHash == target && clearPIN === _clearPIN) {
    // Clear the board
    board = new Array(config.height)
      .fill(0)
      .map(() => new Array(config.width).fill(config.backgroundColor));
    boardString = boardToStrings();

    io.emit("board", { board: boardString });
  }

  //Sign the admin ID
  let adminId = pwHash
    .split("")
    .map((c, i) => c.charCodeAt(0) ^ target.charCodeAt(i))
    .reduce((a, b) => a + b);

  console.log(adminId);

  res.json(ok({ token: sign({ id: adminId }) }));
});
```

Here, the last line is very interesting. It signs a new valid JWT token with an id that gets calculated by user input. This is exactly what we need to get a valid JWT for admin access! Also the signing is not protected by any checks(there is an if condition with `pwHash == target && clearPIN === _clearPIN`, however the signing happens afterwards outside the if condition). 
So now the big question is: what input do we need to give to get an adminId of 0? The adminId is calculated here:
```javascript
  let adminId = pwHash
    .split("")
    .map((c, i) => c.charCodeAt(0) ^ target.charCodeAt(i))
    .reduce((a, b) => a + b);
```
We can get 0 by having `pwHash` being the same as `target`. This is because the xor wil cancel eachother out and the sum will be 0. Howver `target` is the md5 of an unknown value stored in `config.n`. `pwHash` on the other hand is the md5 of a multiple of 2 user-provided inputs. This sounds like an RSA problem and impossible to crack if `conifg.n` is well chosen... So the only way to get an adminId of 0 is by leaking `config.n` somehow...

Looking at the `updateUser` function again, there is some code with which one can access the config. However, there are two problems:
1. This code lies in the same area as the setColor code. Meaning we still need to bypass `isAdmin`
2. `n` and `p` are blacklisted 

1st point I gave up before, but if I managed to bypass the `n` and `p` blacklist, I was very confident that I was on the right track and I would tackle the UTF-8 case-folding again. So, let's analyze the `n` and `p` blacklist code. `n` and `p` are blacklisted by a function similar to this one: 
```javascript
let blacklist = ["p", "n", "port"]; if(!blacklist.includes(userRequest)) return rights[userRequest];
```
As I already knew that the user input can be any JSON object, I opened a javascript console and played around to find a non-string datatype, that can be passed as lookup index to an object and still work. I found that passing an array with a single value worked. So `rights[["n"]]` returned the same result as `rights["n"]`! Furthermore, `blacklist.include(["n"])` returns false, which is exactly what we want.

Now in theory, I had figured everything out. But I couldn't test it on the server as I didn't find a working UTF-8 case folding character. So what to do if you can't find a valid character in the UTF-8 spec but supsect there being one? Exactly: Open a javascript console and try out every single UTF-8 character. Here is the function I wrote:

```javascript
for(i=0;i<100000;i++){ //Increase if needed
    out = String.fromCharCode(i);
		if(out.toLowerCase() == "k" && out.toUpperCase() != "K") console.log(out);
}
```
And I finally got some UTF-8 characters that were "k" in lowercase but not "K" in uppercase. I used \u212A and tada, I bypassed the `isAdmin` check. Furthermore, I bypassed all the other steps that I planned in my head as described above and got a signed JWT token with id = 0! This was all that was needed to finally make a request to /flag and get the flag! 


## Lessons learned
Offline Bruteforcing stuff is sometimes more efficient then reading through specs. Had I tried finding valid UTF-8 characters with a small script right away, I would have saved a lot of time. The UTF-8 spec is huge and finding the right information is not always easy.

I'm very pleased that I solved the other 2 bypasses mentally before I could manage to find the UTF-8 bypass. After finding the UTF-8 bypass, I was excited that the rest of the challenge was working as I already planned in my head.
