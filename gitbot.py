#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import time
import irclib
import urllib2
import threading
from json import loads
from datetime import (datetime, timedelta)
from urllib2 import (urlopen, HTTPError, URLError)
from django.utils.encoding import (smart_str, smart_unicode)

bot_start_time = time.time()

msgqueue = []
bot_owner = ''
network = ''
port = 6667
chan = ''
nick = ''
name = ''
password = ''
kill_bot = 'screen -X -S prebot kill'
token = ''
url_api = ''
hist_ankoa = os.environ.get("HOME") + "/IRC_BOT/prebot/hist_ankoa.entry"


def AnkoA_news():

    git_hist = open(hist_ankoa, "r")
    filetext = git_hist.read()
    git_hist.close()

    try:
        req = urllib2.Request(
            url_api, headers={"Accept": "application/vnd.github.v3+json"})
        req.add_header("Authorization", "token {0}".format(token))
        data = loads(urllib2.urlopen(req).read())
        for entry in data:

            # Global infos
            type = smart_str(entry['type'])
            actor = smart_str(entry['actor']['login'])
            date = '[{}]'.format(str(datetime.now()).split('.')[0])

            # Push Events
            if (type == "PushEvent"):

                branch = smart_str(entry['payload']['ref']).split("/")[2]
                before = smart_str(entry['payload']['before'])[0:10]
                head = smart_str(entry['payload']['head'])[0:10]
                compare = "https://github.com/Ankoa/Your_event/"\
                          "compare/{0}...{1}".format(before, head)
                for item in entry['payload']['commits']:
                    action = smart_str(item['message']).replace('\n\n', ' - ')\
                                                       .replace('\n', ' - ')
                    msg = "\x02[Your_event]\x02 {0} pushed to {1}: {2} > {3}"\
                          .format(actor, branch, action, compare)

                    if (msg not in filetext):
                        git_hist = open(hist_ankoa, "a")
                        git_hist.write("{0}\n".format(msg))
                        git_hist.close()
                        msgqueue.append('{0} \x02{1}\x02'.format(msg, date))

            # Gollum Events
            if (type == "GollumEvent"):

                for item in entry['payload']['pages']:
                    msg = "\x02[Your_event]\x02 {0} {1} {2} > {3} "\
                          "\x02{4}\x02".format(actor, smart_str(item['action']),
                                               smart_str(item['title']),
                                               smart_str(item['html_url']), date)

                    if (msg not in filetext):
                        git_hist = open(hist_ankoa, "a")
                        git_hist.write("{0}\n".format(msg))
                        git_hist.close()
                        msgqueue.append(msg)

            # Pull Request Events
            if (type == "PullRequestEvent"):

                pull_title = smart_str(
                    entry['payload']['pull_request']['title'])
                pull_action = smart_str(entry['payload']['action'])
                pull_url = smart_str(
                    entry['payload']['pull_request']['html_url'])
                msg = "\x02[Your_event]\x02 {0} {1} request: {2} > {3} \x02{4}\x02"\
                      .format(actor, pull_action, pull_title, pull_url, date)

                if (msg not in filetext):
                    git_hist = open(hist_ankoa, "a")
                    git_hist.write("{0}\n".format(msg))
                    git_hist.close()
                    msgqueue.append(msg)

            # Issues Events
            if (type == "IssuesEvent" or type == "IssueCommentEvent"):

                issue_title = smart_str(entry['payload']['issue']['title'])
                issue_action = smart_str(entry['payload']['action'])
                issue_url = smart_str(entry['payload']['issue']['html_url'])
                if (type == "IssueCommentEvent" and issue_action == "created"):
                    issue_action = "commented"
                msg = "\x02[Your_event]\x02 {0} {1} issue: {2} > {3} \x02{4}\x02"\
                      .format(actor, issue_action,
                              issue_title, issue_url, date)

                if (msg not in filetext):
                    git_hist = open(hist_ankoa, "a")
                    git_hist.write("{0}\n".format(msg))
                    git_hist.close()
                    msgqueue.append(msg)

    except (HTTPError, KeyError, URLError, IOError, ValueError) as e:
        server.notice(bot_owner, "\x02[API ERROR]\x02 {0}".format(str(e)))
        pass

    threading.Timer(30.0, AnkoA_news).start()


def on_welcome(server, event):
    if (password):
        server.privmsg("nickserv", "IDENTIFY {0}".format(password))
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
            server.privmsg(author, "n00b {0} ! Tu causes à ton bot là !"
                           .format(author))
    else:
        server.privmsg(author, "Hey {0}, t'as craqué ou quoi ? Tu causes à un"
                       " bot là, spice de n00b !".format(author))


def on_pubmsg(server, event):
    author = irclib.nm_to_n(event.source())
    message = event.arguments()[0].strip()
    arguments = message.split(' ')
    nombreArg = len(arguments)

    if (author == bot_owner and nombreArg == 1 and '!exit' == arguments[0]):
        server.disconnect("\x02See you later girls, just need a break !\x02")
        if (kill_bot):
            os.system(kill_bot)

    elif (author == bot_owner and nombreArg == 1
            and '!uptime' == arguments[0]):
        uptime_raw = round(time.time() - bot_start_time)
        uptime = timedelta(seconds=uptime_raw)
        server.privmsg(chan, "\x02Uptime\x02: {0}".format(uptime))

irclib.DEBUG = 1
irc = irclib.IRC()
server = irc.server()
irc.add_global_handler('welcome', on_welcome)
irc.add_global_handler('kick', on_kick)
irc.add_global_handler('privmsg', on_privmsg)
irc.add_global_handler('pubmsg', on_pubmsg)
server.connect(network, port, nick, ircname=name, ssl=False)
AnkoA_news()


def main():
    while (1):
        while (len(msgqueue) > 0):
            msg_chan = msgqueue.pop()
            server.privmsg(chan, msg_chan)
        time.sleep(1)
        irc.process_once()
        time.sleep(1)

if (__name__ == "__main__"):
    main()
