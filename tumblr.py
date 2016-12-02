#!/usr/bin/python3
# -*- coding:utf-8 -*-

import gevent
import gevent.monkey
from datetime import datetime
from optparse import OptionParser
import requests
import queue
import re
from lxml import etree
import os

USE_PROXY = True
PROXY = {
    "http": "socks5://127.0.0.1:1080",
    "https": "socks5://127.0.0.1:1080"
    }

START = 0
OFFSET = 50
TIMEOUT = 10
RETRY = 1
n = 1
photos_url = queue.Queue(maxsize = 0)
videos_url = queue.Queue(maxsize = 0)

def logger(message):
    msg = '[%s] %s' % (str(datetime.now()), message)
    print (msg)
    with open('tumblr.log', 'a') as f:
        f.write(msg + '\r\n')


def download(site, thread_id, total):
    global n, TIMEOUT, RETRY
    while(not photos_url.empty()):
        url = photos_url.get()
        filename = site + '/photo/' + url.split('/')[-1]
        logger("[T p %d](%d/%d) to download %s" % (thread_id, n, total, filename))
        done_id = n
        n += 1
        retry = 0
        while retry < RETRY:
            try:
                resp = requests.get(url, stream=True, proxies=PROXY, timeout=TIMEOUT)
                with open(filename, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        f.write(chunk)
                logger("[T p %d](%d/%d) Done download %s" % (thread_id, done_id, total, filename))
                break
            except KeyboardInterrupt:
                exit(0)
            except:
                logger("[T p %d](%d/%d) Error download %s" % (thread_id, done_id, total, filename))
            retry += 1

    while(not videos_url.empty()):
        url = videos_url.get()
        try:
            video_id = re.findall('/(\d+)/', url)[0]
        except Exception as e:
            logger('rename %s error, force to: %d' % (url, n))
            video_id = str(n)
        filename = site + '/video/' + video_id + '.mp4'
        logger("[T v %d](%d/%d) to download %s" % (thread_id, n, total, filename))
        done_id = n
        n += 1
        retry = 0
        while retry < RETRY:
            try:
                resp = requests.get(url, stream=True, proxies=PROXY, timeout=TIMEOUT)
                vsize = int(resp.headers['Content-Length']) + 0.01    # force != 0
                writed = 0
                with open(filename, 'wb') as f:
                    flag = {i: False for i in range(0, 101, 10)}
                    for chunk in resp.iter_content(chunk_size=1024):
                        f.write(chunk)
                        writed += 1024
                        persent = int(writed/vsize*100)
                        persent = (persent if persent <= 100 else 100)
                        if persent % 10 == 0 and flag[persent // 10 * 10] == False and persent != 0:
                            logger("[T p %d](%d/%d) [%d%%] %s" % (thread_id, done_id, total, persent, filename))
                            flag[persent // 10 * 10] = True
                logger("[T p %d](%d/%d) Done download %s" % (thread_id, done_id, total, filename))
                break
            except KeyboardInterrupt:
                exit(0)
            except:
                logger("[T p %d](%d/%d) Error download %s" % (thread_id, done_id, total, filename))
            retry += 1

def crawler(site, types):
    def photos():
        start = START
        offset = OFFSET
        links = []
        while(1):
            url = 'http://%s.tumblr.com/api/read?type=photo&num=%d&start=%d' % (site, offset, start)
            html = requests.get(url, proxies=PROXY).text.encode()
            results = etree.HTML(html).xpath('//photo-url/text()')
            get_length = len(results)
            links = links + results
            logger('get %d from %s' % (get_length, url))
            if get_length == 0:
                break
            start += offset
        return list(set(links))


    def videos():
        start = START
        offset = OFFSET
        links = set()
        while(1):
            url = 'http://%s.tumblr.com/api/read?type=video&num=%d&start=%d' % (site, offset, start)
            html = requests.get(url, proxies=PROXY).text.encode()
            results = etree.HTML(html).xpath('//video-player/text()')
            for i in results:
                links.add(re.findall('[\S\s]*src="(\S*)"',i)[0])
            get_length = len(results)
            logger('get %d from %s' % (get_length, url))
            if get_length == 0:
                break
            start += offset
        return list(links)

    if requests.get('http://%s.tumblr.com/' % (site), proxies=PROXY).status_code != 200:
        logger('site:%s response not 200' % (site))
        return 0

    if types == 'photo' or types == 'both':
        for i in photos():
            photos_url.put(i)
    if types == 'video' or types == 'both':
        for i in videos():
            videos_url.put(i)
    return photos_url.qsize() + videos_url.qsize()


def tasks(site, types, thread):
    try:
        os.mkdir(site)
    except Exception as e:
        logger(str(e))
    total = crawler(site, types)

    threads = [gevent.spawn(download, site, i, total) for i in range(thread)]
    gevent.joinall(threads)


if __name__ == "__main__":
    gevent.monkey.patch_all()
    parser = OptionParser()
    parser.add_option("-s", "--sites",
                        help="sites split with ',', example:2013117,66666")
    parser.add_option("--type",
                        help="[photo|video|both]")
    parser.add_option("--thread",
                        help="threads")
    parser.add_option("--proxy",
                        help="socks5://127.0.0.1:1080")

    (options, args) = parser.parse_args()
    if options.proxy:
        PROXY = {
                "http": options.proxy,
                "https": options.proxy
                }
    if options.sites == None or options.type not in {'photo', 'video', 'both'}:
        parser.print_help()
        exit(0)
    else:
        for site in options.sites.split(','):
            tasks(site, options.type, int(options.thread))
