# tumblr_download

```base
pip3 install lxml gevent PySocks
```
- - -
    Usage: tumblr.py [options]

    Options:
      -h, --help            show this help message and exit
      -s SITES, --sites=SITES
                            sites split with ',', example:2013117,66666
      --type=TYPE           [photo|video|both]
      --thread=THREAD       threads
      --proxy=PROXY         socks5://127.0.0.1:1080

- - -
    can be changed in source file:
    RETRY: retry times, default 1
    PROXY: because G.F.W must use proxy
    TIMEOUT: time to wait net IO

- - -

    example:
      python3 tumblr.py -s 2013117,66666 --type=both --thread=10
- - -

    API:
      http://{site}.tumblr.com/api/read?type={photo|video}&num={pagesize}&start={start}
