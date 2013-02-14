import os
from datetime import datetime, timedelta


def isInt(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


def isFloat(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


def GetTextTime(second):
    sec = timedelta(seconds=int(second))
    d = datetime(1,1,1) + sec
    txt = ''
    if d.day-1 > 0:
        txt = "%d DAYS : %d HOURS : %d MIN : %d SEC" % (d.day-1, d.hour, d.minute, d.second)
    elif d.hour > 0:
        txt = "%d HOURS : %d MIN : %d SEC" % (d.hour, d.minute, d.second)
    elif d.minute > 0:
        txt = "%d MIN : %d SEC" % (d.minute, d.second)
    else:
        txt = "%d SEC" % (d.second)

    return txt


def timestamp2ReadableString(ts):
    return ts.strftime('%Y-%m-%d')


def createFile(fileName, content):
    fd = os.open(fileName, os.O_RDWR|os.O_CREAT)
    os.write(fd, content)
    os.close(fd)