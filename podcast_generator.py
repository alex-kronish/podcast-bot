import random
import re
import xmltodict
from bs4 import BeautifulSoup
import json
import twitter
import requests
import markov
import urllib.parse


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
    st = "visibility=public&status=" + urllib.parse.quote(inputmsg)
    conn = requests.post(url, st, headers=headers)
    return conn


def gettitles(urls):
    # regex to try and strip episode numbers
    # rss/channel/item[]/title
    headers = {"Accept": "*/*", "User-Agent": "Podcastacular/1.0"}
    patterns = [r"^Episode\s",
                r"^[0-9]+[: -]+",
                r"^[0-9]+[: -]+",
                r"^MBMBaM [0-9]+: ",
                r"^Giant Bombcast [0-9]+ ",
                r"^Giant Bombcast ",
                r"Face 2 Face: ",
                r"My Brother, My Brother And Me: ",
                r"The Adventure Zone:\s",
                r"The The Adventure Zone:"
                r"^Run Button Podcast [0-9]+\s[:-] ",
                r"^RB Podcast [0-9]+[: -]+ ",
                r"^Talking Simpsons - ",
                r"^[a-zA-Z]+\s[0-9]+[: -]+ ",
                r"[0-9]+[: -]+",
                r":$",
                r"^Talking Simpsons - ",
                r"^Disenchantment - ",
                r"^[0-9]+[: -]+",
                r"^Episode [0-9]+[: -]+",
                r"^Ep [0-9]+: ",
                r"^Ep. [0-9]+: "
                r"^[0-9]+ - "
                r"\*[Pp][Rr][Ee][Vv][Ii][Ee][Ww]\* ",
                r"\*Preview\*",
                r"\*PREVIEW\*",
                r"^Ep. ",
                r"^Sawbones: ",
                r"^Ep. [0-9]+. ",
                r"^BEST SHOW BESTS #",
                r"^Best Show Bests #"]

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
                tmp = t
                for p in patterns:
                    tmp = re.sub(p, "", tmp)
                tmp = re.sub(r'[Ff][Ee][Aa][Tt]\.?', "featuring", tmp)
                tmp = re.sub(r'[Ff][Tt]\.?', "featuring", tmp)
                tmp = re.sub(r'[Pp][Tt]\.?', "part", tmp)
                titles.append(tmp)
    # f = open("podcast_titles_sample.txt", "wt")
    # for items in titles:
    #    f.write(items + "\n")
    # f.close()
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


def generatepodcaststring(ep, title, descr, service_len):
    output = str(ep) + ": " + title.title() + "\n\n" + descr
    if len(output) >= service_len:
        output = output[:(service_len - 4)] + "..."  # twitter is bad imo
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
    desc_range = random.randint(3, 5)
    desc_f = ""
    for a in range(1, desc_range):
        if len(desc_f) <= 200:
            desc_tmp = mkv_desc.generate_sentence()
            desc_f = desc_f + desc_tmp + " "

    desc_f = re.sub(r"@", "", desc_f)
    final_title = re.sub(r"[: ,\-.?]$", "!", final_title)
    fake_podcast_m = generatepodcaststring(epnum, final_title, desc_f, 500).encode("latin-1", errors="replace").decode(
        "latin-1", errors="replace")
    fake_podcast_t = generatepodcaststring(epnum, final_title, desc_f, 280).encode("latin-1", errors="replace").decode(
        "latin-1", errors="replace")
    print(fake_podcast_m)

    tw = twitterpost(fake_podcast_t)
    mstdn = mastoapipost(fake_podcast_m)
    # print(mstdn.content)
