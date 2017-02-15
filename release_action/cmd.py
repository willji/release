# coding=utf-8
from core.common import get_ftp_info, get_salt_result, get_result, logger, RETCODE, STDOUT, ReleaseStep, try_except, \
    ReleaseError
from release_action.api import LBApi, HBApi, CmdControlApi
import httplib


class CmdBase(object):
    cmd_name, ftp_info, send_data = None, None, None
    ftp_flag, arg_format = '_package', '%s#production/%s/%s/%s#%s'
    version_result = False
    rs_method = get_salt_result

    def __init__(self, host, location, item_type, dep, item, version):
        self.dep = dep
        self.host = host
        self.item = item
        self.item_type = item_type
        self.location = location
        self.version = version
        logger.info('%s' % self.cmd_name)

    def set_ftp_info(self, ftp_flag='_package'):
        self.ftp_info = get_ftp_info(self.location + ftp_flag)

    def set_send_data(self, arg_format='%s#production/%s/%s/%s#%s'):
        self.send_data = {
            'host': self.host,
            'module_name': self.cmd_name,
            'arg': arg_format % (self.item_type, self.dep, self.item, self.version, self.ftp_info)
        }

    def set_rs_method(self):
        if self.version_result:
            self.rs_method = self.get_version_result
        else:
            self.rs_method = get_salt_result

    def run(self):
        logger.debug('%s' % self.cmd_name)
        self.set_ftp_info(ftp_flag=self.ftp_flag)
        self.set_send_data(arg_format=self.arg_format)
        self.set_rs_method()
        logger.info('send_data:%s' % self.send_data)
        try:
            result = CmdControlApi().post(self.send_data)
        except Exception, e:
            logger.error('run error: %s' % str(e))
            result = e.message
        return self.rs_method(result, self.host)

    def get_version_result(self, m_result, *args):
        if m_result[RETCODE] == 0:
            t_result = m_result[STDOUT][self.host]
            if isinstance(t_result, dict) and RETCODE in t_result:
                if t_result[STDOUT] == self.version:
                    result = get_result(0, '%s' % self.version)
                else:
                    result = get_result(1, 'wrong version,current version is %s' % t_result[STDOUT])
            else:
                result = get_result(1, t_result)
        else:
            result = m_result
        return result


class CmdGetPackage(CmdBase):
    cmd_name = ReleaseStep.GetPackage


class CmdComplete(CmdBase):
    cmd_name = ReleaseStep.Complete
    version_result = True


class CmdVersionCheck(CmdBase):
    cmd_name = ReleaseStep.VersionCheck
    version_result = True


class CmdRollBack(CmdBase):
    cmd_name = ReleaseStep.RollBack


class CmdUploadProduction(CmdBase):
    cmd_name = ReleaseStep.UploadProduction
    ftp_flag = '_production'
    arg_format = '%s#%s/%s/%s#%s'


class CmdUpdate(CmdBase):
    cmd_name = ReleaseStep.Update


class CmdGetProduction(CmdBase):
    cmd_name = ReleaseStep.GetProduction
    ftp_flag = '_production'
    arg_format = '%s#%s/%s/%s#%s'


class CmdGetConfiguration(CmdBase):
    cmd_name = ReleaseStep.GetConfiguration
    ftp_flag = '_configuration'
    arg_format = '%s#configuration/%s/%s/STAGING_PROD/%s#%s'


class CmdLB(CmdBase):
    cmd_query = None

    def __init__(self, host, location, item, cmd_query):
        self.host = host
        self.location = location
        self.item = item
        self.cmd_query = cmd_query

    def lb_up(self):
        return self.run(ops='lb-up')

    def lb_down(self):
        return self.run(ops='lb-down')

    def lb_add(self):
        return self.run(ops='lb-add')

    def get_lbgroup(self):
        app_path = '/api/cmdb/applications/applicationgroup?application__name=%s&location__name=%s&environment__name=Production' % (
        self.item, self.location)
        app_result = self.cmd_query.get(app_path)
        return app_result['results'][0]['lbgroup']

    def get_load_balance(self, name):
        app_path = '/api/cmdb/devices/lbgroup?name=%s' % name
        app_result = self.cmd_query.get(app_path)
        return app_result['results'][0]['loadbalancers']

    def get_load_balance_ip(self, name):
        app_path = '/api/cmdb/devices/loadbalancer?name=%s' % name
        app_result = self.cmd_query.get(app_path)
        return app_result['results'][0]['ipaddresses']

    def set_lbgroup(self):
        rs = dict()
        for group in self.get_lbgroup():
            rs[group] = [self.get_load_balance_ip(lb)[0] for lb in self.get_load_balance(group)]
        return rs

    @try_except
    def run(self, ops):
        lbgroup = self.set_lbgroup()
        if lbgroup:
            data = dict(app=self.item, host=[dict(ip=self.host)], ops=ops, lbgroup=lbgroup, type='nginx')
            return LBApi().post(path='/api/lb/cli/', data=data)
        else:
            raise NameError('can not find this item\'s lbgroup setting in %s' % self.item)

    def __set_send_data(self, lbgroup, ops):
        return dict(item=self.item, host=self.host, ops=ops, lbgroup=lbgroup)


class CmdWarm(CmdBase):
    cmd_query = None

    def __init__(self, host, item, cmd_query):
        self.host = host
        self.item = item
        self.cmd_query = cmd_query
        self.app_path = '/api/cmdb/applications/application?name=%s' % self.item
        self.app_result = self.cmd_query.get(self.app_path)

    @try_except
    def run(self):
        if self.app_result['count'] == 1:
            res = self.app_result['results'][0]
            try:
                port = int(res.get("port", 80))
            except Exception,e:
                logger.error(str(e))
                port = 80
            warmup_urls = res['warmup_urls']
            if not warmup_urls:
                all_status = True
                warm_url = ''
            else:
                warm_url = ''
                all_status = True
                for m in warmup_urls:
                    logger.debug(m)
                    t_result = self.check(self.host, port, 'http://%s:%s%s' % (self.item, port, m["warmup_url"]),
                                          m["expected_codes"], m["expected_text"])
                    # if t_result:
                    #     pass
                    # else:
                    if not t_result:
                        warm_url = m
                        all_status = False
                        break
            if all_status:
                return get_result(0, 'done')
            else:
                raise ReleaseError('warm this url %s failed' % warm_url)
        else:
            raise ReleaseError('can not find this item in %s' % self.app_path)

    @staticmethod
    def check(host, port, url, expected_codes, expected_text, method='GET'):
        conn = httplib.HTTPConnection(host, port)
        conn.connect()
        conn.request(method, url)
        resp = conn.getresponse()
        code = resp.status
        logger.debug('url%s ,expect_code  type %s, code %s' % (url, expected_codes, code))
        flag = False
        if expected_codes:
            if str(code) in [str(x) for x in expected_codes]:
                flag = True
            else:
                raise ReleaseError('%s code not in  %s ' % (str(code), [str(x) for x in expected_codes]))
        if expected_text:
            if str(expected_text) in resp.read():
                flag = True
            else:
                raise ReleaseError('%s not found  %s ' % (str(expected_text), url))
        return flag


class CmdHbCheck(CmdBase):
    def __init__(self, host, item):
        self.host = host
        self.item = item

    def set_send_data(self):
        self.send_data = {
            'host': self.host,
            'url': 'http://%s/hb' % self.item
        }

    @try_except
    def run(self):
        return CmdControlApi().post(self.send_data)
