#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import time
import irclib
import urllib2
import threading
import feedparser
from BeautifulSoup import BeautifulSoup
from urllib2 import (urlopen, HTTPError, URLError)
from django.utils.encoding import (smart_str, smart_unicode)

bot_owner = '' # maybe you ! :p
network = ''
port = 6667
chan = '#test'
nick = 'prebot'
name = 'P2P Feedback News'
password = '' # nickserv password
kill_bot = '' # When screen in use... 'screen -X -S screen_name kill'
msgqueue = [] # please, leave this empty ! :p
hist = os.environ.get("HOME")+"/prebot/hist.entry"

PRE = "" # PRE Announce from : https://pre.corrupt-net.org/ passkey needed !
SCC = "" # what's this ?
GFT = "" # what's that ?
HDT = "" # who's this ?
CHD = "" # who's that ?
ST_EU = "https://www.sous-titres.eu/films.xml"
SUBSCENE = "http://v2.subscene.com/subtitles/french/historybylanguage.aspx"
SUBSYNC = "http://www.subsynchro.com/les-20-derniers-sous-titres-ajoutes.xml"
OPENSUB = "http://www.opensubtitles.org/fr/search/sublanguageid-fre/searchonlymovies-on/rss_2_00"

def update_sources():
    get_hist = open(hist, "r")
    filetext = get_hist.read()
    get_hist.close()
    try:
        pre = feedparser.parse(PRE)
        for entry in pre.entries:
            cat = smart_str(entry.title).split(']')[0].strip().replace('[', '')
            title = smart_str(entry.title).split(']')[1].strip()
            value = re.search(r'S[0-9]{2}E[0-9]{2}', title)
            if (value is None) and ((cat == "DVDR" or cat == "BLURAY")\
                    or (cat == "X264" and "bluray" in title.lower())):
                verif = "[PRE] %s" % title
                if (verif.lower() not in filetext.lower()):
                    size = smart_str(entry.description).replace('<br />', '')\
                                                       .replace('Size', ' | Size').strip()
                    pretime = smart_str(entry.published).replace('+0000', '').strip()
                    hour_utc = pretime.split(' ')[4].split(':')[0]
                    if (hour_utc == "21"):
                        hour_fr = "00"
                    elif (hour_utc == "22"):
                        hour_fr = "01"
                    elif (hour_utc == "23"):
                        hour_fr = "02"
                    else:
                        hour_fr = int(hour_utc)+3
                        hours = "3 4 5 6 7 8 9"
                        if str(hour_fr) in hours:
                            hour_fr = "0%s" % hour_fr
                    pubdate = pretime.replace(hour_utc, str(hour_fr))
                    id = "[PRE] %s [ %s ] %s" % (title, size, pubdate)
                    get_hist = open(hist, "a")
                    get_hist.write("%s\n" % id)
                    get_hist.close()
                    msgqueue.append(id)

        scc = feedparser.parse(SCC)
        for entry in scc.entries:
            title = smart_str(entry.title).strip()
            link = smart_str(entry.link).strip()
            id = "[SCC] %s : %s" % (title, link)
            if (id.lower() not in filetext.lower()):
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        gft = feedparser.parse(GFT)
        for entry in gft.entries:
            title = smart_str(entry.title).strip()
            link = smart_str(entry.link).strip()
            id = "[GFT] %s : %s" % (title, link)
            if (id.lower() not in filetext.lower()):
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        st_eu = feedparser.parse(ST_EU)
        for entry in st_eu.entries:
            title = smart_str(entry.title).strip()
            link = smart_str(entry.link).strip()
            id = "[ST-EU] %s : %s" % (title, link)
            if (id.lower() not in filetext.lower()):
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        subscene = BeautifulSoup(urlopen(SUBSCENE))
        for entry in subscene.findAll('dt', id='a1W'):
            data = entry.find('a')
            title = data.get('title').split('-')[1].strip()
            link = "http://subscene.com%s" % data.get('href').strip()
            id = "[SUBSCENE] %s : %s" % (smart_str(title), smart_str(link))
            if (id.lower() not in filetext.lower()):
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        subsync = feedparser.parse(SUBSYNC)
        for entry in subsync.entries:
            title = smart_str(entry.title).strip()
            verif = "[SUBSYNC] %s" % title
            if (verif.lower() not in filetext.lower()):
                link = smart_str(entry.link).strip()
                id = "[SUBSYNC] %s : %s" % (title, link)                
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        opensub = feedparser.parse(OPENSUB)
        for entry in opensub.entries:
            title = smart_str(entry.title).split('-')[0].strip()
            link = smart_str(entry.link).strip()
            id = "[OPENSUB] %s : %s" % (title, link)
            if (id.lower() not in filetext.lower()):
                get_hist = open(hist, "a")
                get_hist.write("%s\n" % id)
                get_hist.close()
                msgqueue.append(id)

        hdt = feedparser.parse(HDT)
        for entry in hdt.entries:
            title = smart_str(entry.title).strip()
            if ("1080p" in title and "XXX" not in title)\
                    and ("bluray" in title.lower() or "blu-ray" in title.lower()):
                link = smart_str(entry.link).strip()
                verif = link.split('id=')[1]
                if (verif.lower() not in filetext.lower()):
                    id = "[HDT] %s : %s" % (title, link)
                    get_hist = open(hist, "a")
                    get_hist.write("%s\n" % id)
                    get_hist.close()
                    msgqueue.append(id)

        chd = feedparser.parse(CHD)
        for entry in chd.entries:
            title = smart_str(entry.title).strip()
            link = smart_str(entry.link).strip()
            if ("HDTV" not in title and "PDTV" not in title):
                id = "[CHD] %s : %s" % (title, link)
                if (id.lower() not in filetext.lower()):
                    get_hist = open(hist, "a")
                    get_hist.write("%s\n" % id)
                    get_hist.close()
                    msgqueue.append(id)

    except (HTTPError, KeyError, URLError) as e:
        server.notice(bot_owner, "[Feedback Error] "+str(e))
        pass

    threading.Timer(30.0, update_sources).start()

def on_welcome(server, event):
    if (password):
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

    if (author == bot_owner and nombreArg == 1 and '!exit' == arguments[0]):
        server.disconnect("See you later girls, just need a break !")
        if (kill_bot):
            os.system(kill_bot)

irclib.DEBUG = 1
irc = irclib.IRC()
server = irc.server()
irc.add_global_handler ('welcome', on_welcome)
irc.add_global_handler ('kick', on_kick)
irc.add_global_handler ('privmsg', on_privmsg)
irc.add_global_handler ('pubmsg', on_pubmsg)
server.connect(network, port, nick, ircname=name, ssl=False)

update_sources()

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
