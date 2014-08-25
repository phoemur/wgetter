#!/usr/bin/env python

"""
Wgetter is another command line download utility written completely in python.
It is based on python-wget (https://bitbucket.org/techtonik/python-wget/src) with some improvements.
It works on python >= 2.6 or python >=3.0 Runs on Windows or Linux or Mac

API Usage:

>>> import wgetter
>>> filename = wgetter.download('https://sites.google.com/site/doctormike/pacman-1.2.tar.gz', outdir='/home/user')
100 % [====================================================>] 19.9KiB / 19.9KiB  100.0KiB/s  eta 0:00:01
>>> filename
'/home/user/pacman-1.2.tar.gz'
"""

import sys
import os
import shutil
import tempfile
import hashlib
import datetime

from time import time

PY3K = sys.version_info >= (3, 0)

if PY3K:
    import urllib.request as ulib
    import urllib.parse as urlparse
else:
    import urllib2 as ulib
    import urlparse

SUFFIXES = {1000: ['KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'],
            1024: ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB']}


def approximate_size(size, a_kilobyte_is_1024_bytes=True):
    '''
    Humansize.py from Dive into Python3
    Mark Pilgrim - http://www.diveintopython3.net/
    Copyright (c) 2009, Mark Pilgrim, All rights reserved.

    Convert a file size to human-readable form.
    Keyword arguments:
    size -- file size in bytes
    a_kilobyte_is_1024_bytes -- if True (default), use multiples of 1024
    if False, use multiples of 1000
    Returns: string
    '''

    size = float(size)

    if size < 0:
        raise ValueError('number must be non-negative')

    multiple = 1024 if a_kilobyte_is_1024_bytes else 1000
    for suffix in SUFFIXES[multiple]:
        size /= multiple
        if size < multiple:
            return '{0:.1f}{1}'.format(size, suffix)

    raise ValueError('number too large')


def get_console_width():
    """Return width of available window area. Autodetection works for
       Windows and POSIX platforms. Returns 80 for others

       Code from http://bitbucket.org/techtonik/python-pager
    """

    if os.name == 'nt':
        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        # get console handle
        from ctypes import windll, Structure, byref
        try:
            from ctypes.wintypes import SHORT, WORD, DWORD
        except ImportError:
            # workaround for missing types in Python 2.5
            from ctypes import (
                c_short as SHORT, c_ushort as WORD, c_ulong as DWORD)
        console_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

        # CONSOLE_SCREEN_BUFFER_INFO Structure
        class COORD(Structure):
            _fields_ = [("X", SHORT), ("Y", SHORT)]

        class SMALL_RECT(Structure):
            _fields_ = [("Left", SHORT), ("Top", SHORT),
                        ("Right", SHORT), ("Bottom", SHORT)]

        class CONSOLE_SCREEN_BUFFER_INFO(Structure):
            _fields_ = [("dwSize", COORD),
                        ("dwCursorPosition", COORD),
                        ("wAttributes", WORD),
                        ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", DWORD)]

        sbi = CONSOLE_SCREEN_BUFFER_INFO()
        ret = windll.kernel32.GetConsoleScreenBufferInfo(
            console_handle, byref(sbi))
        if ret == 0:
            return 0
        return sbi.srWindow.Right + 1

    elif os.name == 'posix':
        from fcntl import ioctl
        from termios import TIOCGWINSZ
        from array import array

        winsize = array("H", [0] * 4)
        try:
            ioctl(sys.stdout.fileno(), TIOCGWINSZ, winsize)
        except IOError:
            pass
        return (winsize[1], winsize[0])[0]

    return 80

CONSOLE_WIDTH = get_console_width()

# Need 2 spaces more to avoid linefeed on Windows
AVAIL_WIDTH = CONSOLE_WIDTH - 59 if os.name == 'nt' else CONSOLE_WIDTH - 57


def filename_from_url(url):
    """:return: detected filename or None"""
    fname = os.path.basename(urlparse.urlparse(url).path)
    if len(fname.strip(" \n\t.")) == 0:
        return None
    return fname


def filename_from_headers(headers):
    """Detect filename from Content-Disposition headers if present.
    http://greenbytes.de/tech/tc2231/

    :param: headers as dict, list or string
    :return: filename from content-disposition header or None
    """
    if type(headers) == str:
        headers = headers.splitlines()
    if type(headers) == list:
        headers = dict([x.split(':', 1) for x in headers])
    cdisp = headers.get("Content-Disposition")
    if not cdisp:
        return None
    cdtype = cdisp.split(';')
    if len(cdtype) == 1:
        return None
    if cdtype[0].strip().lower() not in ('inline', 'attachment'):
        return None
    # several filename params is illegal, but just in case
    fnames = [x for x in cdtype[1:] if x.strip().startswith('filename=')]
    if len(fnames) > 1:
        return None
    name = fnames[0].split('=')[1].strip(' \t"')
    name = os.path.basename(name)
    if not name:
        return None
    return name


def filename_fix_existing(filename, dirname):
    """Expands name portion of filename with numeric ' (x)' suffix to
    return filename that doesn't exist already.
    """
    name, ext = filename.rsplit('.', 1)
    names = [x for x in os.listdir(dirname) if x.startswith(name)]
    names = [x.rsplit('.', 1)[0] for x in names]
    suffixes = [x.replace(name, '') for x in names]
    # filter suffixes that match ' (x)' pattern
    suffixes = [x[2:-1] for x in suffixes
                if x.startswith(' (') and x.endswith(')')]
    indexes = [int(x) for x in suffixes
               if set(x) <= set('0123456789')]
    idx = 1
    if indexes:
        idx += sorted(indexes)[-1]
    return '{0}({1}).{2}'.format(name, idx, ext)


def report_bar(bytes_so_far, total_size, speed, eta):
    '''
    This callback for the download function is used to print the download bar
    '''
    percent = int(bytes_so_far * 100 / total_size)
    current = approximate_size(bytes_so_far).center(9)
    total = approximate_size(total_size).center(9)
    shaded = int(float(bytes_so_far) / total_size * AVAIL_WIDTH)
    sys.stdout.write(
        " {0}% [{1}{2}{3}] {4}/{5} {6} eta{7}".format(str(percent).center(4),
                                                      '=' * (shaded - 1),
                                                      '>',
                                                      ' ' * (AVAIL_WIDTH - shaded),
                                                      current,
                                                      total,
                                                      (approximate_size(speed) + '/s').center(11),
                                                      eta.center(10)))
    sys.stdout.write("\r")
    sys.stdout.flush()
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')


def report_unknown(bytes_so_far, total_size, speed, eta):
    '''
    This callback for the download function is used
    when the total size is unknown
    '''
    sys.stdout.write(
        "Downloading: {0} / Unknown - {1}/s\r".format(approximate_size(bytes_so_far),
                                                      approximate_size(speed)))

    sys.stdout.write("\r")
    sys.stdout.flush()
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')


def report_onlysize(bytes_so_far, total_size, speed, eta):
    '''
    This callback for the download function is used when console width
    is not enough to print the bar.
    It prints only the sizes
    '''
    percent = int(bytes_so_far * 100 / total_size)
    current = approximate_size(bytes_so_far).center(10)
    total = approximate_size(total_size).center(10)
    sys.stdout.write('D: {0}% -{1}/{2}'.format(percent, current, total) + "eta {0}".format(eta))
    sys.stdout.write("\r")
    sys.stdout.flush()
    if bytes_so_far >= total_size:
        sys.stdout.write('\n')


def md5sum(filename, blocksize=8192):
    '''
    Returns the MD5 checksum of a file
    '''
    with open(filename, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(blocksize)
            if not data:
                break
            m.update(data)
        return m.hexdigest()


def download(link, outdir='.', chunk_size=4096):
    '''
    This is the Main function, which downloads a given link
    and saves on outdir (default = current directory)
    '''
    url = None
    fh = None
    eta = 'unknown '
    bytes_so_far = 0
    filename = filename_from_url(link) or "."

    # get filename for temp file in current directory
    (fd_tmp, tmpfile) = tempfile.mkstemp(
        ".tmp", prefix=filename + ".", dir=outdir)
    os.close(fd_tmp)
    os.unlink(tmpfile)

    try:
        url = ulib.urlopen(link)
        fh = open(tmpfile, mode='wb')

        headers = url.info()
        try:
            total_size = int(headers['Content-Length'])
        except (ValueError, KeyError, TypeError):
            total_size = 'unknown'

        try:
            md5_header = headers['Content-MD5']
        except (ValueError, KeyError, TypeError):
            md5_header = None

        # Define which callback we're gonna use
        if total_size != 'unknown':
            if CONSOLE_WIDTH > 57:
                reporthook = report_bar
            else:
                reporthook = report_onlysize
        else:
            reporthook = report_unknown

        # Below are the registers to calculate network transfer rate
        time_register = time()
        speed = 0.0
        speed_list = []
        bytes_register = 0.0
        eta = 'unknown '

        # Loop that reads in chunks, calculates speed and does the callback to
        # print the progress
        while True:
            chunk = url.read(chunk_size)
            # Update Download Speed every 1 second
            if time() - time_register > 1:
                speed = (bytes_so_far - bytes_register) / \
                    (time() - time_register)
                speed_list.append(speed)

                # Set register properly for future use
                time_register = time()
                bytes_register = bytes_so_far

                # Estimative of remaining download time
                if total_size != 'unknown' and len(speed_list) == 3:
                    speed_mean = sum(speed_list) / 3
                    eta_sec = int((total_size - bytes_so_far) / speed_mean)
                    eta = str(datetime.timedelta(seconds=eta_sec))
                    speed_list = []

            bytes_so_far += len(chunk)

            if not chunk:
                break

            fh.write(chunk)
            reporthook(bytes_so_far, total_size, speed, eta)
    except KeyboardInterrupt:
        print('\n\nCtrl + C: Download aborted by user')
        print('Partial downloaded file:\n{0}'.format(os.path.abspath(tmpfile)))
        sys.exit(1)
    finally:
        if url:
            url.close()
        if fh:
            fh.close()

    filenamealt = filename_from_headers(headers)
    if filenamealt:
        filename = filenamealt

    # add numeric '(x)' suffix if filename already exists
    if os.path.exists(os.path.join(outdir, filename)):
        filename = filename_fix_existing(filename, outdir)
    filename = os.path.join(outdir, filename)

    shutil.move(tmpfile, filename)

    # Check if sizes matches
    if total_size != 'unknown' and total_size != bytes_so_far:
        print(
            '\n\nWARNING!! Downloaded file size mismatches... Probably corrupted...')

    # Check md5 if it was in html header
    if md5_header:
        print('\nValidating MD5 checksum...')
        if md5_header == md5sum(filename):
            print('MD5 checksum passed!')
        else:
            print('MD5 checksum do NOT passed!!!')

    return filename

if __name__ == '__main__':
    if len(sys.argv) == 1 or sys.argv[1] in {'-h', '--help'}:
        print('Usage: {0} <URL>'.format(sys.argv[0]))

    args = [str(elem) for elem in sys.argv[1:]]

    for link in args:
        print('Downloading ' + link)
        filename = download(link)
        print('\nSaved under {0}'.format(filename))
