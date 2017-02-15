# coding=utf-8
import ConfigParser
import httplib
import json
import os
import urllib2
from urllib import urlencode

from core.common import logger, try_except
from ops.settings import API_CONFIG_PATH

ContentType_Form = "application/x-www-form-urlencoded"

ContentType_Json = "application/json"

RestApiSite = ('release', 'cmdb', 'jira', 'lb')

CmdApiSite = ('hb', 'cmd_control')


class BaseApi(object):
    type_list = None
    error_info = None
    content_type = ContentType_Json
    port = 80
    path, host, user, passwd, auth_data = None, None, None, None, None
    auth_header = None

    def __init__(self, cfg_type):
        cf_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), API_CONFIG_PATH)
        self.cf = ConfigParser.ConfigParser()
        self.cf.read(cf_file)
        if cfg_type in self.type_list:
            self.init(self.cf.get(cfg_type, "path"), self.cf.get(cfg_type, "host"), self.cf.get(cfg_type, "user"), self.cf.get(cfg_type, "passwd"))
        else:
            self.error_info('no this type %s' % cfg_type)
            logger.error(self.error_info)

    def init(self, path, host, user, passwd):
        self.path = path
        self.host = host
        self.user = user
        self.passwd = passwd
        self.auth_data = {
            'username': self.user,
            'password': self.passwd,
        }
        self.auth_header = {"Authorization": "Token %s" % str(self.get_token()), "Content-Type": self.content_type}

    def get_token(self):
        header = {"Content-Type": ContentType_Json}
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.connect()
        content = json.dumps(self.auth_data)
        conn.request('POST', self.path, content, header)
        result = conn.getresponse().read()
        conn.close()
        return json.loads(result)['token']


class RestApi(BaseApi):
    type_list = RestApiSite

    def __init__(self, cfg_type):
        super(RestApi, self).__init__(cfg_type)

    @try_except
    def __request(self, method, path, data=None):
        conn = httplib.HTTPConnection(self.host, self.port)
        conn.connect()
        send_data = ''
        if data:
            send_data = json.dumps(data)
            print send_data
        conn.request(method, path, send_data, self.auth_header)
        logger.debug('access: %s%s data :%s %s' % (self.host, path, data, self.auth_header))
        result = conn.getresponse().read()
        conn.close()

        print result
        return json.loads(result)

    def get(self, path):
        return self.__request('GET', path)

    def post(self, path, data):
        return self.__request('POST', path, data)

    def update(self, path, data):
        return self.__request('PATCH', path, data)

    def create(self, path, data):
        return self.__request('POST', path, data)

    def delete(self, path):
        return self.__request('DELETE', path)


class FormBaseApi(BaseApi):
    content_type = ContentType_Form
    cmd_path = None

    @try_except
    def post(self, data):
        content = urlencode(data)
        req = urllib2.Request(self.cmd_path, content, self.auth_header)
        result = urllib2.urlopen(req)
        result_content = result.read()
        logger.debug('path:%s data:%s' % (self.cmd_path, content))
        logger.debug(result_content)
        return json.loads(result_content)


class CmdApi(FormBaseApi):
    type_list = CmdApiSite

    def __init__(self, cfg_type):
        super(CmdApi, self).__init__(cfg_type)
        if cfg_type in self.type_list:
            self.cmd_path = self.cf.get(cfg_type, "cmd_path")


class LBApi(RestApi):
    def __init__(self):
        super(LBApi, self).__init__('lb')


class HBApi(CmdApi):
    def __init__(self):
        super(HBApi, self).__init__('hb')


class CmdControlApi(CmdApi):
    def __init__(self):
        super(CmdControlApi, self).__init__('cmd_control')


class CmdbApi(RestApi):
    def __init__(self):
        super(CmdbApi, self).__init__('cmdb')


class JiraApi(RestApi):
    def __init__(self):
        super(JiraApi, self).__init__('jira')


class ReleaseApi(FormBaseApi):
    def __init__(self, path='/api/token/', host='127.0.0.1', user='demo', passwd='demo', cmd_path=None):
        self.init(path=path, host=host, user=user, passwd=passwd, cmd_path=cmd_path)

    def init(self, path, host, user, passwd, cmd_path=None):
        self.cmd_path = cmd_path
        super(ReleaseApi, self).init(path, host, user, passwd)
