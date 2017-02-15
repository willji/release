# -*- coding:utf8 -*-
import chardet
import httplib
import codecs
import json
import os
import re
from os.path import getsize
import platform
import urllib


def all():
    plat = platform.system()
    if (plat == "Windows"):
        path = 'D:\\logfiles'
        cut_str = '\\'
    else:
        cut_str = '/'
        path = '/usr/local/log'
    result = []
    for m in os.walk(path, followlinks=True):
        if m[2]:
            for n in m[2]:
                info = m[0] + cut_str + n
                if re.match(".*tar$", info):
                    pass
                elif re.match(".*zip$", info):
                    pass
                elif re.match(".*gz$", info):
                    pass
                elif re.match(".*rar$", info):
                    pass
                else:
                    try:
                        mtime = str(int(os.path.getmtime(info)))
                        size = getsize(info)
                        if size < 1024:
                            info_size = str(size) + 'b'
                        elif size < 1048576:
                            info_size = str(size / 1024) + 'kb'
                        else:
                            info_size = str(size / 1048576) + 'mb'

                        new_info = info + '||' + info_size + '||' + mtime

                        result.append(new_info)
                    except:
                        pass
    return sorted(result, cmp=lambda x, y: cmp(y.split('||')[2], x.split('||')[2]))[0:200]


def get(path):
    result = []
    plat = platform.system()
    #    tt=open(path,'rb')
    #    ff=tt.read(100)
    #    content=chardet.detect(ff)
    #    code_content=content['encoding']
    #    tt.close()
    if (plat == "Windows"):
        default_code = 'gbk'
    else:
        default_code = 'utf8'
    #    with codecs.open(path,mode='rb',encoding=code_content) as f:
    f = open(path, mode='rb')
    all = f.readlines()
    length = len(all)
    if length > 1000:
        result = all[-1000:-1]
    else:
        result = all
    new_result = []
    for m in result:
        code = chardet.detect(m)
        if code['encoding'] == None:
            code_content = default_code
        else:
            code_content = code['encoding']
        new = m.decode(code_content, 'ignore').encode('utf-8')
        new_result.append(new)
    return new_result


def net_stat():
    plat = platform.system()
    if (plat == "Windows"):
        result = os.popen('netstat -an').read()
        new = result.decode('gb2312').encode('utf-8')
        return new
    else:
        result = os.popen('netstat -an').read()
        return result


def ps_stat():
    plat = platform.system()
    if (plat == "Windows"):
        return __salt__['cmd.script']('salt://scripts/GetProcess.ps1', shell='powershell')
    else:
        cmd = 'top -n 1 -b'
        result = os.popen(cmd).read()
        new = result.decode('ascii').encode('utf-8')
        return new


def test_ping(host):
    plat = platform.system()
    if (plat == "Windows"):
        cmd = 'ping %s' % host
        result = os.popen(cmd).read()
        new = result.decode('gb2312').encode('utf-8')
        return new
    else:
        cmd = 'ping %s -c 4' % host
        result = os.popen(cmd).read()
        return result


def get_http_status(host, path, port):
    header = {"Content-Type": "application/json"}
    conn = httplib.HTTPConnection(host, port)
    conn.connect()
    conn.request('GET', path, '', header)
    result = conn.getresponse()
    status = result.status
    header = result.getheaders()
    all = {'status': status, 'header': header}
    conn.close()
    return all


def get_http_content(path):
    res = urllib.urlopen(path)
    header_res = {}
    info = res.info()
    for m in res.info().keys():
        header_res[m] = info.get(m)
    status = res.getcode()
    content_res = res.read()
    result = {
        'status': status,
        'headers': header_res,
        'content': content_res
    }
    return result
