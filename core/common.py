# coding=utf-8
import os
import ConfigParser
from ops.settings import FTP_CONF
import logging

STDOUT = 'stdout'

STDERR = 'stderr'

RETCODE = 'retcode'

LOCATION_INFO = {
    u"外高桥IDC6_package": 'w_idc6_package',
    u"外高桥IDC6_configuration": 'w_idc6_configuration',
    u"外高桥IDC6_production": 'w_idc6_production',

    u"T1_package": 'T1_package',
    u"T1_configuration": 'T1_configuration',
    u"T1_production": 'T1_production',

    u"T1-1_package": 'T1_package',
    u"T1-1_configuration": 'T1_configuration',
    u"T1-1_production": 'T1_production',

    u"T1-2_package": 'T1_package',
    u"T1-2_configuration": 'T1_configuration',
    u"T1-2_production": 'T1_production',

    u"T2_package": 'T2_package',
    u"T2_configuration": 'T2_configuration',
    u"T2_production": 'T2_production',

    u"T3_package": 'T3_package',
    u"T3_configuration": 'T3_configuration',
    u"T3_production": 'T3_production',
}

EXEC_NAME = {
    'one': '一键发布',
    'gray': '灰度发布'
}


class ExecName(object):
    one = '一键发布'
    gray = '灰度发布'


STATUS_LIST = {
    'undo': 0,
    'processing': 1,
    'suspend': 2,
    'failed': 3,
    'done': 4
}


def get_ftp_info(location):
    cf = ConfigParser.ConfigParser()
    cf.read(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), FTP_CONF))
    host = cf.get(LOCATION_INFO[location], "host")
    user = cf.get(LOCATION_INFO[location], "user")
    password = cf.get(LOCATION_INFO[location], "password")
    result = host + ',' + user + ',' + password
    return result


def get_result(retcode, result):
    if retcode == 0:
        return dict(retcode=retcode, stderr='', stdout=result)
    else:
        return dict(retcode=retcode, stderr=result, stdout='')


def get_salt_result(data, host):
    if data[RETCODE] == 0:
        m_result = data[STDOUT][host]
        if isinstance(m_result, dict) and RETCODE in m_result:
            result = m_result
        else:
            result = get_result(1, m_result)
    else:
        result = data
    return result


logger = logging.getLogger('release')


class ReleaseError(Exception):
    pass


def try_except(func):
    def wrapped(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception, e:
            print str(e)
            result = get_result(1, str(e))
        finally:
            return result

    return wrapped


class ReleaseEnv(object):
    Staging = 'Staging'
    Production = 'Production'


class ReleaseStep(object):
    Complete = 'complete'
    GetPackage = 'get_package'
    GetConfiguration = 'get_configuration'
    GetProduction = 'get_production'
    Update = 'update'
    UploadProduction = 'upload_production'
    RollBack = 'rollback'
    VersionCheck = 'version_check'
    LBAdd = 'lb_add'


class ReleaseApiStep(object):
    LBDown = 'lb-down'
    LBUp = 'lb-up'
    HBCheck = 'hb_check'
    Warm = 'warm'
    LBAdd = 'lb-add'


class ReleaseStatus(object):
    Processing = 'processing'
    Undo = 'undo'
    Done = 'done'
    Failed = 'failed'
    Suspend = 'suspend'


class ReleaseType(object):
    UpdateStg = 'updatestg'
    UpdateIIS = 'updateiis'
    UpdateSrv = 'updatesrv'
    RollBack = 'roll'
    ExpandIIS = 'expandiis'
    ExpandSrv = 'expandsrv'
