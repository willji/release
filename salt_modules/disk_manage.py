# -*- coding:utf-8 -*-
# __author__='guziqiang'
# __create_time__ = '2016/11/3'

import os
import time
import urllib2
import json
import subprocess
import re
import glob
import logging
from logging.handlers import RotatingFileHandler

FILENAME = 'C:\salt\logfiles-remove.log' if os.name == 'nt' else '/var/log/salt/logfiles-remove.log'
BACKUP_COUNT = 5
FORMAT = '%(asctime)s %(levelname)s %(module)s %(funcName)s-[%(lineno)d] %(message)s'
LOG_LEVEL = logging.INFO
MAX_BYTES = 10 * 1024 * 1024
HANDLER = RotatingFileHandler(FILENAME, mode='a', maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
FORMATTER = logging.Formatter(FORMAT)
HANDLER.setFormatter(FORMATTER)
logger = logging.getLogger('disk_manage')
logger.setLevel(LOG_LEVEL)
logger.addHandler(HANDLER)

Z_URL = 'http://10.11.251.34:11000/rule/select/?app='
TOKEN = '1bfc0978761df126e8925ca3552c2b68e59b7dce'


class ClearFiles(object):
    def get_apps_info(self, apps):
        '''
        :param apps:[app1,app2]
        :return: {app:{
                      "/usr/local/log/xxxxx": {
                        "is_re": false,
                        "match": ".*",
                        "before": 7,
                        "recursive": true,
                        "remove_empty_dir": true
                      },
                      "/usr/local/log/yyyy": {
                        "is_re": false,
                        "match": ".*",
                        "before": 7,
                        "recursive": true,
                        "remove_empty_dir": true
                      }
                    }
                }
        '''
        ret = {}
        for app in apps:
            if not app: continue
            res = self.http_get(app)
            ret[app] = res
        return ret

    def http_get(self, app):
        try:
            url = '%s%s' % (Z_URL, app)
            req = urllib2.Request(url)
            req.add_header("Authorization", "token %s" % TOKEN)
            res = urllib2.urlopen(req).read()
            return json.loads(res)
        except Exception, e:
            logger.error('http_get %s error:%s' % (app, str(e)))
            return False

    def check_disk(self):
        '''
        :return: {"c:":"50","d:":"20","/":"20"}
        '''
        ret = {}
        if os.name == 'nt':
            cmd = "wmic logicaldisk where mediatype='12' get deviceid,freespace,size"
            res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.readlines()
            for i in res[1:]:
                if i.replace('\r\r\n', '') and len(i):
                    label, free, size = i.split()
                    f_free = float(free)
                    f_size = float(size)
                    ret['%s' % label] = int(((f_size - f_free) / f_size) * 100)
        else:
            cmd = "df -P |sed -n '%s' | awk '%s'" % ('2,$p', '{print $6\":\"$5}')
            res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().split('\n')
            for i in res:
                if not i: continue
                s = i.split(":")
                ret[s[0]] = s[1].replace('%', '')
        return ret

    def size_nice_str(self, size):
        for cutoff, label in [(1024 * 1024 * 1024, 'GB'), (1024 * 1024, 'MB'), (1024, 'KB')]:
            if size >= cutoff:
                return "%s%s" % (size / cutoff, label)
        else:
            return size

    def rm_file(self, path, before):
        stat = os.stat(path)
        if self.is_before(stat.st_mtime, before):
            try:
                file_info = '%s||%s||%s' % (path, self.size_nice_str(stat.st_size),
                                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)))
                os.remove(path)
                logger.info('del file:%s' % file_info)
                return file_info
            except Exception, e:
                logger.error('del file:%s-->%s' % (path, str(e)))
                return False
        else:
            logger.error('can not delete this file:%s,because less %s days ' % (path, before))
            return False

    def rm_dir(self, path, is_rm_e_dir):
        if is_rm_e_dir and self.is_empty(path):
            try:
                os.rmdir(path)
                logger.info('del dir:%s%s' % (path, os.sep))
                return True
            except Exception, e:
                logger.error('del dir:%s-->%s' % (path, str(e)))
                return False
        else:
            logger.error('Can not delete this directory:%s,because condition is %s or this Directory is not empty' % (
                path, is_rm_e_dir))
            return False

    def args_verify(self, *args):
        '''
        :param args: pattern, is_recursive, is_remove_empty_dir, before, is_re
        :return: bool
        '''
        if None in args: return False
        if not (len(args[0]) and args[0] != '*.*'
                and type(args[1]) == bool
                and type(args[2]) == bool
                and type(args[3]) == int
                and type(args[4]) == bool):
            return False
        logger.info("args verify success!")
        return True

    def is_empty(self, path):
        return False if os.listdir(r'%s' % path) else True  # if empty is True

    def is_before(self, st_mtime, before):
        # file_tm_yday = time.localtime(st_mtime).tm_yday
        # now_tm_yday = time.localtime().tm_yday
        # # return True if (now_tm_yday - file_tm_yday) > int(before) else False
        return (time.time() - st_mtime) > int(before) * 24 * 3600

    def is_root_dir(self, path):
        ret = False
        path_split = path.split(os.sep)
        lens = len(path_split)

        if os.name == 'nt':
            black_list = ["windows", "program files"]
        else:
            black_list = ["root", "boot", "etc", "proc", "bin", "lib", "sbin"]

        if lens == 1:
            ret = True
        elif lens > 1 and path_split[1].lower() in black_list:
            ret = True
        return ret

    def regular_remove(self, path, pattern, is_recursive, is_remove_empty_dir, before):
        res = []
        compile = re.compile(pattern)
        if is_recursive:
            for i in os.walk(path, topdown=False):
                # ('D:\\test\\a\\c', [], [])
                # ('D:\\test\\a', ['c'], ['b.log'])
                # ('D:\\test', ['a'], ['a.log'])
                _sub_path = i[0]
                if i[2]:
                    for filename in i[2]:
                        t_file = _sub_path + os.sep + filename
                        if not compile.match(filename):
                            logger.info('can match %s'%t_file)
                            continue
                        is_success = self.rm_file(t_file, before)
                        if is_success: res.append(is_success)
                else:
                    is_success = self.rm_dir(_sub_path, is_remove_empty_dir)
                    if is_success: res.append(_sub_path)
        else:
            file_list = os.listdir(path)  # ['a', 'a.log', 'b']
            for name in file_list:
                if not compile.match(name):
                    continue
                _sub_path = path + os.sep + name
                if os.path.isfile(_sub_path):  # is file
                    is_success = self.rm_file(_sub_path, before)
                    if is_success: res.append(is_success)
                else:
                    is_success = self.rm_dir(_sub_path, is_remove_empty_dir)
                    if is_success: res.append(_sub_path)

        return res

    def glob_remove(self, path, pattern, is_recursive, is_remove_empty_dir, before):
        res = []
        if is_recursive:
            for i in os.walk(path, topdown=False):
                # ('D:\\test\\a\\c', [], [])
                # ('D:\\test\\a', ['c'], ['b.log'])
                # ('D:\\test', ['a'], ['a.log'])
                _sub_path = i[0]
                if i[2]:
                    globs = glob.glob(_sub_path + os.sep + pattern)
                    for filename in i[2]:
                        t_file = _sub_path + os.sep + filename
                        if t_file in globs:
                            is_success = self.rm_file(t_file, before)
                            if is_success: res.append(is_success)
                else:
                    is_success = self.rm_dir(_sub_path, is_remove_empty_dir)
                    if is_success: res.append(_sub_path)
        else:
            file_list = os.listdir(path)  # ['a', 'a.log', 'b']
            globs = glob.glob(path + os.sep + pattern)
            for name in file_list:
                _sub_path = path + os.sep + name
                if os.path.isfile(_sub_path) and _sub_path in globs:  # is file
                    is_success = self.rm_file(_sub_path, before)
                    if is_success: res.append(is_success)
        return res

    def remove(self, app_info):
        '''
        :param app_info: {"/usr/local/log/xxxxx": {
                            "is_re": false,
                            "match": ".*",
                            "before": 7,
                            "recursive": true,
                            "remove_empty_dir": true},
                          "/usr/local/log/yyyy": {
                            "is_re": false,
                            "match": ".*",
                            "before": 7,
                            "recursive": true,
                            "remove_empty_dir": true}
                        }
        :return:[]
        '''
        res = []
        for path, value in app_info.items():

            if not os.path.exists(path):
                logger.error('%s is not exists' % path)
                continue

            if self.is_root_dir(path):
                logger.error('%s is root dir' % path)
                continue

            logger.info('%s:%s' % (path, json.dumps(value)))

            pattern = value.get("match", None)
            is_re = value.get("is_re", None)
            is_recursive = value.get("recursive", None)
            is_remove_empty_dir = value.get("remove_empty_dir", None)
            before = value.get("before", None)

            verify = self.args_verify(pattern, is_recursive, is_remove_empty_dir, before, is_re)
            if not verify:
                logging.info('args verify is fail')
                continue  # verify is False break

            if is_re:
                res += self.regular_remove(path, pattern, is_recursive, is_remove_empty_dir, before)
            else:
                res += self.glob_remove(path, pattern, is_recursive, is_remove_empty_dir, before)
        return res

    def run(self, apps):
        '''
        :param apps: 'app1,app2'
        :return: {"remove_files":["file1_path","file2_path"],"disk_info":{"c":"50","d":"20","/":"20"}}
        '''
        try:
            logger.info('args:%s' % apps)
            if apps:
                msg = {"remove_files": []}
                msg["disk_info"] = self.check_disk()
                _apps = apps.split(',')
                apps_info = self.get_apps_info(_apps)
                for app_info in apps_info.values():
                    files = self.remove(app_info)
                    msg["remove_files"] += files
                return msg
            else:
                logger.error('app is none')
                return 'app is none'

        except Exception, e:
            logger.error('exec error %s' % str(e))
            return 'exec error'


def del_files(apps):
    return ClearFiles().run(apps)
