About
======

Wgetter is another command line download utility written completely in python.
It is based on python-wget (https://bitbucket.org/techtonik/python-wget/src)
with some improvements.

It works on python >= 2.6 or python >=3.0
Runs on Windows or Linux


Usage
======

    python -m wgetter <URL>


API Usage
======

    >>> import wgetter
    >>> filename = wgetter.download('https://sites.google.com/site/doctormike/pacman-1.2.tar.gz')
    100 % [====================================================>] 19.9KiB / 19.9KiB  100.0KiB/s  
    >>> filename
    'pacman-1.2.tar.gz'

Changelog
========

0.2 (2014-03-06)
 * Init version, uses urllib2 instead of urlretrieve (deprecated), reads in chunks with network transfer rate calculation.
   Fancy bar. Human readable file-sizes. Checks Md5 if available and download final size.
   It's a heavy modification of python-wget made for my needs that i decided to share.
