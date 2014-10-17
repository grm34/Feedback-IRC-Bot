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
bot_start_time = time.time()
network = ''
port = 6667
chan = '#test'
nick = 'prebot'
name = 'P2P Feedback News'
password = '' # nickserv password
kill_bot = '' # When screen in use... 'screen -X -S screen_name kill'
msgqueue = [] # please, leave this empty ! :p
hist_sources = os.environ.get("HOME")+"/prebot/hist.entry"

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
    get_hist = open(hist_sources, "r")
    filetext = get_hist.read()
    get_hist.close()
    try:
        pre = feedparser.parse(PRE)
        for entry in pre.entries:
            cat = smart_str(entry.title).split(']')[0].strip().replace('[', '')
            title = smart_str(entry.title).split(']')[1].strip()
            value = re.search(r'S[0-9]{2}E[0-9]{2}', title)
            if (value is None and (
                    cat == "DVDR" or cat == "BLURAY"
                    or cat == "X264" and "bluray" in title.lower())):
                verif = "[PRE] {0}".format(title)
                if (verif.lower() not in filetext.lower()):
                    size = smart_str(
                        entry.description).replace('<br />', '')\
                                          .replace('Size', ' | Size').strip()
                    pretime = smart_str(
                        entry.published).replace('+0000', '').strip()
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
                            hour_fr = "0{0}".format(hour_fr)
                    pubdate = pretime.replace(hour_utc, str(hour_fr))
                    msg = "[PRE] {0} [ {1} ] {2}".format(title, size, pubdate)
                    get_hist = open(hist_sources, "a")
                    get_hist.write("{0}\n".format(msg))
                    get_hist.close()
                    msgqueue.append(msg)

        scc = feedparser.parse(SCC)
        for entry in scc.entries:
            link = smart_str(entry.link).strip()
            if (smart_str(link) not in filetext):
                title = smart_str(entry.title).strip()
                msg = "[SCC] {0} : {1}".format(title, link)
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        gft = feedparser.parse(GFT)
        for entry in gft.entries:
            title = smart_str(entry.title).strip()
            verif = "[GFT] {0}".format(title)
            if (verif.lower() not in filetext.lower()):
                link = smart_str(entry.link).strip()
                msg = "[GFT] {0} : {1}".format(title, link)
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        st_eu = feedparser.parse(ST_EU)
        for entry in st_eu.entries:
            link = smart_str(entry.link).strip()
            if (smart_str(link) not in filetext):
                title = smart_str(entry.title).strip()
                msg = "[ST-EU] {0} : {1}".format(title, link)
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        subscene = BeautifulSoup(urlopen(SUBSCENE))
        for entry in subscene.findAll('dt', id='a1W'):
            data = entry.find('a')
            link = "http://subscene.com{0}".format(data.get('href').strip())
            if (smart_str(link) not in filetext):
                title = data.get('title').split('-')[1].strip()
                msg = "[SUBSCENE] {0} : {1}".format(smart_str(title),
                                                    smart_str(link))
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        subsync = feedparser.parse(SUBSYNC)
        for entry in subsync.entries:
            title = smart_str(entry.title).strip()
            verif = "[SUBSYNC] {0}".format(title)
            if (verif.lower() not in filetext.lower()):
                link = smart_str(entry.link).strip()
                msg = "[SUBSYNC] {0} : {1}".format(title, link)
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        opensub = feedparser.parse(OPENSUB)
        for entry in opensub.entries:
            link = smart_str(entry.link).strip()
            if (smart_str(link) not in filetext):
                title = smart_str(entry.title).split('-')[0].strip()
                msg = "[OPENSUB] {0} : {1}".format(title, link)
                get_hist = open(hist_sources, "a")
                get_hist.write("{0}\n".format(msg))
                get_hist.close()
                msgqueue.append(msg)

        hdt = feedparser.parse(HDT)
        for entry in hdt.entries:
            title = smart_str(entry.title).strip()
            if ("1080p" in title and "XXX" not in title and (
                    "bluray" in title.lower() or "blu-ray" in title.lower())):
                link = smart_str(entry.link).strip()
                verif = link.split('id=')[1]
                if (verif.lower() not in filetext.lower()):
                    msg = "[HDT] {0} : {1}".format(title, link)
                    get_hist = open(hist_sources, "a")
                    get_hist.write("{0}\n".format(msg))
                    get_hist.close()
                    msgqueue.append(msg)

        chd = feedparser.parse(CHD)
        for entry in chd.entries:
            title = smart_str(entry.title).strip()
            if ("HDTV" not in title and "PDTV" not in title):
                link = smart_str(entry.link).strip()
                if (smart_str(link) not in filetext):
                    msg = "[CHD] {0} : {1}".format(title, link)
                    get_hist = open(hist_sources, "a")
                    get_hist.write("{0}\n".format(msg))
                    get_hist.close()
                    msgqueue.append(msg)

    except (HTTPError, KeyError, URLError, IOError, ValueError) as e:
        server.notice(bot_owner, "[RSS ERROR] {0}".format(str(e)))
        pass

    threading.Timer(20.0, update_sources).start()
    
    
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
        server.disconnect("See you later girls, just need a break !")
        if (kill_bot):
            os.system(kill_bot)

    elif (author == bot_owner and nombreArg == 1
            and '!uptime' == arguments[0]):
        uptime_raw = round(time.time() - bot_start_time)
        uptime = timedelta(seconds=uptime_raw)
        server.privmsg(chan, "\x02Uptime\x02: up {0}".format(uptime))

irclib.DEBUG = 1
irc = irclib.IRC()
server = irc.server()
irc.add_global_handler('welcome', on_welcome)
irc.add_global_handler('kick', on_kick)
irc.add_global_handler('privmsg', on_privmsg)
irc.add_global_handler('pubmsg', on_pubmsg)
server.connect(network, port, nick, ircname=name, ssl=False)

update_sources()    


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
