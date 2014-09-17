#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import json
import irclib
import urllib2
import threading
from json import loads
from urllib2 import (Request, urlopen, URLError, HTTPError)
from django.utils.encoding import (smart_str, smart_unicode)

bot_owner = ''                                          #--> Bot owner
network = ''                                            #--> Server IRC
port = 6667                                             #--> Server Port
chan = '#test'                                          #--> Server Channel
nick = ''                                               #--> Bot Nick
name = 'GitHub Feedback'                                #--> Bot Description
password = ''                                           #--> Bot Nickserv password
token = ''                                              #--> GitHub API Token
url_api = 'https://api.github.com/repos/XXX/XXX/events' #--> GitHub API Repos URL
kill_bot = ''                                           #--> When screen in use

hist = os.environ.get("HOME")+"/gitbot/git_hist.entry"

def on_welcome(server, event):
    if password:
        server.privmsg("nickserv", "IDENTIFY %s" % password)
    server.privmsg("chanserv", "SET irc_auto_rejoin ON")
    server.privmsg("chanserv", "SET irc_join_delay 0")
    server.join(chan)

def on_kick(server, event):
    server.join(chan)

def on_privmsg(server, event):
    author = irclib.nm_to_n(event.source())
    message = event.arguments()[0].strip()
    arguments = message.split(' ')
    nombreArg = len(arguments)

    if (author == bot_owner):
        if ('!say' == arguments[0]):
            server.privmsg(chan, message.replace('!say', '')[1:])
        elif ('!act' == arguments[0]):
            server.action(chan, message.replace('!act', '')[1:])
        elif ('!j' == arguments[0]):
            server.join(message[3:])
        elif ('!p' == arguments[0]):
            server.part(message[3:])
        else:
            server.privmsg(author, "n00b "+author+" ! "
                "Tu causes à ton bot là !")
    else:
        server.privmsg(author, "Hey "+author+", t'as craqué ou quoi ? "\
            "Tu causes à un bot là, spice de n00b !")

def on_pubmsg(server, event):
    author = irclib.nm_to_n(event.source())
    message = event.arguments()[0].strip()
    arguments = message.split(' ')
    nombreArg = len(arguments)

    if (author == bot_owner):
        if (nombreArg == 1 and '!exit' == arguments[0]):
            server.disconnect("See you later girls, just need a break !")
            if (kill_bot):
                os.system(kill_bot)

irclib.DEBUG = 1
irc = irclib.IRC()
irc.add_global_handler ('welcome', on_welcome)
irc.add_global_handler ('kick', on_kick)
irc.add_global_handler ('privmsg', on_privmsg)
irc.add_global_handler ('pubmsg', on_pubmsg)

server = irc.server()
server.connect(network, port, nick, ircname=name, ssl=False)

msgqueue = []

def update_api():
    git_hist = open(hist, "r")
    filetext = git_hist.read()
    git_hist.close()
    try:
        req = urllib2.Request(url_api,
                              headers={"Accept": "application/vnd.github.v3+json"})
        req.add_header("Authorization", "token %s" % token)
        data = loads(urllib2.urlopen(req).read())
        for entry in data:

            # Global infos
            type = smart_str(entry['type'])
            actor = smart_str(entry['actor']['login'])
            temp = "["+smart_str(entry['created_at']).replace("-", "/")\
                                                     .replace("T", "-")\
                                                     .replace("Z", "")+"]"
            hour_utc = temp.split("-")[1].split(":")[0]
            if (hour_utc == "21"):
                hour_fr = "00"
            elif (hour_utc == "22"):
                hour_fr = "01"
            elif (hour_utc == "23"):
                hour_fr = "02"
            else:
                hour_fr = int(hour_utc)+2
                hours = "3 4 5 6 7 8 9"
                if str(hour_fr) in hours:
                    hour_fr = "0%s" % hour_fr
            date = temp.replace(hour_utc, str(hour_fr))

            # Push Events
            if (type == "PushEvent"):
                branch = smart_str(entry['payload']['ref']).split("/")[2]
                before = smart_str(entry['payload']['before'])[0:10]
                head = smart_str(entry['payload']['head'])[0:10]
                compare = "https://github.com/grm34/AnkoA/"\
                          "compare/%s...%s" % (before, head)
                for item in entry['payload']['commits']:
                    action = smart_str(item['message']).replace('\n\n', ' - ')
                    id = "[Push Event] "+actor+" pushed to "+branch+\
                         ": "+action+" -> "+compare+" "+date
                    if (id not in filetext):
                        git_hist = open(hist, "a")
                        git_hist.write(id + "\n")
                        git_hist.close()
                        msgqueue.append(id)

            # Gollum Events
            if (type == "GollumEvent"):
                for item in entry['payload']['pages']:
                    id = "[Wiki Event] "+actor+" "+smart_str(item['action'])+\
                         " "+smart_str(item['title'])+" -> "+\
                         smart_str(item['html_url'])+" "+date
                    if (id not in filetext):
                        git_hist = open(hist, "a")
                        git_hist.write(id + "\n")
                        git_hist.close()
                        msgqueue.append(id)

            # Pull Request Events
            if (type == "PullRequestEvent"):
                pull_title = smart_str(entry['payload']['pull_request']['title'])
                pull_action = smart_str(entry['payload']['action'])
                pull_url = smart_str(entry['payload']['pull_request']['html_url'])
                id = "[Request Event] "+actor+" "+pull_action+" request: "+\
                     pull_title+" -> "+pull_url+" "+date
                if (id not in filetext):
                    git_hist = open(hist, "a")
                    git_hist.write(id + "\n")
                    git_hist.close()
                    msgqueue.append(id)

            # Issues Events
            if (type == "IssuesEvent" or type == "IssueCommentEvent"):
                issue_title = smart_str(entry['payload']['issue']['title'])
                issue_action = smart_str(entry['payload']['action'])
                issue_url = smart_str(entry['payload']['issue']['html_url'])
                if (type == "IssueCommentEvent" and issue_action == "created"):
                    issue_action = "commented"
                id = "[Issue Event] "+actor+" "+issue_action+" issue: "+\
                     issue_title+" -> "+issue_url+" "+date
                if (id not in filetext):
                    git_hist = open(hist, "a")
                    git_hist.write(id + "\n")
                    git_hist.close()
                    msgqueue.append(id)

    except (HTTPError, KeyError, URLError) as e:
        server.notice(bot_owner, "[API ERROR] "+str(e))
        pass

    threading.Timer(30.0, update_api).start()

update_api()

def main():
    while (1):
        while (len(msgqueue) > 0):
            msg = msgqueue.pop()
            server.privmsg(chan, msg)
        time.sleep(1)
        irc.process_once()
        time.sleep(1)

if (__name__ == "__main__"):
    main()
