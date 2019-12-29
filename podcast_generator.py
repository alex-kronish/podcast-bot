import random
import re
import xmltodict
from bs4 import BeautifulSoup
import json
import twitter
import requests
import markov


def parseconf(fname):
    f = open("configuration/" + fname, "rt")
    conf = json.load(f)
    f.close()
    return conf


def twitterpost(inputmsg):
    tw_api = twitter.Api(consumer_key=apikeys["twitter"]["api_consumer_key"],
                         consumer_secret=apikeys["twitter"]["api_consumer_secret"],
                         access_token_key=apikeys["twitter"]["api_access_token"],
                         access_token_secret=apikeys["twitter"]["api_access_token_secret"])
    tw_status = tw_api.PostUpdate(inputmsg)
    return tw_status


def mastoapipost(inputmsg):
    token = apikeys["mastodon"]["api_access_token"]
    url = apikeys["mastodon"]["post_url"] + token
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    st = "visibility=public&status=" + inputmsg
    conn = requests.post(url, st, headers=headers)
    return conn


def gettitles(urls):
    # regex to try and strip episode numbers
    # rss/channel/item[]/title
    headers = {"Accept": "*/*","User-Agent": "Podcastacular/1.0"}
    patterns = ["^Episode\s",
                "^[0-9]+[: -]+\s",
                "^[0-9]+\s[: -]+\s",
                "^MBMBaM [0-9]+:\s",
                "^Giant Bombcast [0-9]+:\s",
                "^Giant Bombcast\s",
                "Face 2 Face:\s",
                "My Brother, My Brother And Me:\s",
                "The Adventure Zone:\s",
                "The The Adventure Zone:"
                "^Run Button Podcast [0-9]+\s[:-]\s",
                "^RB Podcast [0-9]+[: -]+\s",
                "^Talking Simpsons -\s",
                "^[a-zA-Z]+\s[0-9]+[: -]+\s",
                "[0-9]+[: -]+",
                ":$",
                "[a-zA-Z\s]+[0-9]+"]

    titles = []
    for u in urls:
        r = requests.get(u, timeout=25, headers=headers)
        r.encoding = "utf-8"
        if r.status_code != 200:
            print("Something went wrong connecting to URL: " + u + ". Got a status code of: " + str(r.status_code))
        else:
            # print(r.content)
            x = xmltodict.parse(r.content)
            items = x["rss"]["channel"]["item"]
            ts = []
            for i in items:
                ts.append(i["title"])

            for t in ts:
                for p in patterns:
                    tmp = re.sub(p, "", t)
                titles.append(tmp)
    return titles


def getdescriptions(urls):
    # rss/channel/item[]/description
    descr = []
    headers = {"Accept": "*/*", "User-Agent": "Podcastacular/1.0"}
    for u in urls:
        r = requests.get(u, timeout=25, headers=headers)
        r.encoding = "utf-8"
        if r.status_code != 200:
            print("Something went wrong connecting to URL: " + u)
        else:
            # print(r.content)
            x = xmltodict.parse(r.content)
            items = x["rss"]["channel"]["item"]
            ds = []
            for i in items:
                ds.append(i["description"])

            for d in ds:
                # there could be stray HTML in the description, since line breaks and links and stuff are technically
                # allowed in RSS feeds, lets use bs4 to clean it.
                if d is not None:
                    soup = BeautifulSoup(d, features="html.parser")
                    tmp = soup.get_text()
                    tmp2 = re.sub("For information regarding your data privacy, visit acast.", "", tmp)
                    descr.append(tmp2)
    return descr


def generatepodcaststring(ep, title, descr):
    output = str(ep) + ": " + title.title() + "\n\n" + descr
    if len(output) >= 280:
        output = output[:276] + "..."  # twitter is bad imo
    return output


if __name__ == "__main__":
    sourcefeeds = parseconf("rss_sources.json")
    apikeys = parseconf("api_keys_secret.json")
    source_titles = []
    source_desc = []
    mkv_title = markov.MarkovChainer(2)
    mkv_desc = markov.MarkovChainer(2)
    in_titles = gettitles(sourcefeeds["rss_feeds"])
    in_desc = getdescriptions(sourcefeeds["rss_feeds"])
    for t in in_titles:
        mkv_title.add_text(t)
    for d in in_desc:
        mkv_desc.add_text(d)
    for t in range(0, 10):
        final_title = mkv_title.generate_sentence()
    epnum = random.randint(1, 500)
    desc_range = random.randint(3, 7)
    desc_f = ""
    for a in range(1, desc_range):
        desc_tmp = mkv_desc.generate_sentence()
        desc_f = desc_f + desc_tmp + " "
    fake_podcast = generatepodcaststring(epnum, re.sub("[: ,\-.?]$", "!", final_title),
                                         desc_f).encode("latin-1", errors="replace").decode("latin-1", errors="replace")

    print(fake_podcast)

    tw = twitterpost(fake_podcast)
    mstdn = mastoapipost(fake_podcast)
    # print(mstdn.content)
