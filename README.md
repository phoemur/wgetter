About
========

Wgetter is another command line download utility written completely in python.
It is based on python-wget (https://bitbucket.org/techtonik/python-wget/src)
with some improvements.

It works on python >= 2.6 or python >=3.0
Runs on Windows or Linux


Usage
========

    python -m wgetter <URL>


API Usage
========

    >>> import wgetter
    >>> filename = wgetter.download('https://sites.google.com/site/doctormike/pacman-1.2.tar.gz', outdir='/home/user')
    100 % [====================================================>] 19.9KiB / 19.9KiB  100.0KiB/s  eta 0:00:01
    >>> filename
    '/home/user/pacman-1.2.tar.gz'
    
Obs.: If not set, output directory (outdir) defaults to current directory

Installation
========

Using PIP:
    
    pip install wgetter

Manually:

Get the tarball at
    
    https://github.com/phoemur/wgetter/tarball/0.5.1
    
or git clone
    
    git clone https://github.com/phoemur/wgetter.git
    
Then
    
    python setup.py install
    
Changelog
========

0.6 (2015-03-07)
 * Some Bug Fixes

0.5.1 (2014-08-25)
 * Added improved bar and estimated transfer time

0.3 (2014-03-08)
 * Added the option to set download's output directory

0.2 (2014-03-06)
 * Init version, uses urllib2 instead of urlretrieve (deprecated), reads in chunks with network transfer rate calculation.
   Fancy bar. Human readable file-sizes. Checks Md5 if available and download final size.
   It's a heavy modification of python-wget made for my needs that i decided to share.
