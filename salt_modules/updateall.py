import re
import datetime
import zipfile
from ftplib import FTP
import os
import md5


def sumfile(fobj):
    m = md5.new()
    while True:
        d = fobj.read(8096)
        if not d:
            break
        m.update(d)
    return m.hexdigest()


def md5sum(fname):
    try:
        f = file(fname, 'rb')
    except:
        return False
    ret = sumfile(f)
    f.close()
    return ret


def modify(file):
    new_version = datetime.datetime.now().strftime("%y%m%d%H%M")
    fp = open(file, 'r')
    alllines = fp.readlines()
    fp.close()
    fp = open(file, 'w')
    for eachline in alllines:
        a = re.sub('new_version', new_version, eachline)
        fp.writelines(a)
    fp.close()


def extract(file, dir):
    f = zipfile.ZipFile(file, 'r')
    for m in f.namelist():
        f.extract(m, dir)


def unpack(item, id):
    version = item.split('/')[-1]
    node = item.split('/')[-2]
    file = '/opt/tmp/' + item + '/' + version + '.zip'
    md5file = '/opt/tmp/' + item + '/' + version + '.md5'
    f = open(md5file)
    content = f.read()
    f.close()
    newmd5 = content.split(' ')[0]
    md5value = md5sum(file)
    if newmd5 == md5value:
        new_path = '/usr/local/' + node + '/' + version
        extract(file, new_path)
        result = True
        return result
    else:
        result = False
        return result


def start_app(appid):
    status = os.system('/usr/local/deploy/%s/start.sh' % appid)
    return status


def stop_app(appid):
    status = os.system('/usr/local/deploy/%s/stop.sh' % appid)
    return status


def change_link(appid, version):
    os.chdir('/usr/local/%s' % appid)
    status = os.system('rm default -f && ln -s %s default' % version)
    return status


def new(type, appid, taskid):
    if type == 'iis':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "NewSite")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif type == 'service':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "NewService")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif type == 'handler':
        result = 'retcode:\n0'
        return result
    elif type == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            os.system('mkdir /usr/local/%s -p' % node)
            os.chdir('/usr/local/%s' % node)
            os.system('ln -s %s default' % version)
            start_status = start_app(node)
            result = 'retcode:\n0'
            return result
        except:
            result = 'retcode:\n1'
            return result
    else:
        result = 'retcode:\n1'
        return result


def update(typeid, appid, taskid):
    if typeid == 'iis':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "UpdateSite")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "UpdateService")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        result = 'retcode:\n0'
        return result
    elif typeid == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            os.chdir('/usr/local/%s' % node)
            stop_status = stop_app(node)
            if stop_status == 0:
                update_status = change_link(node, version)
                if update_status == 0:
                    start_status = start_app(node)
                    if start_status == 0:
                        result = 'retcode:\n0'
                        return result
                    else:
                        result = 'retcode:\n1\n start failed'
                        return result
                else:
                    result = 'retcode:\n1\n change link failed'
                    return result
            else:
                result = 'retcode:\n1\n stop failed'
                return result
        except:
            result = 'retcode:\n1'
            return result
    else:
        result = 'retcode:\n1no this typeid'
        return result


def get_package(typeid, appid, taskid):
    if typeid == 'iis':
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'nodejs':
        all = appid.split('/')
        item = all[-2]
        version_info = all[-1]
        if 'cfg' in version_info.lower():
            version = version_info.split('_')[0]
            downloaddir = appid.split('_')[0]
        else:
            downloaddir = appid
            version = version_info
        try:
            file = version + '.zip'
            md5file = version + '.md5'
            ftp = FTP('10.10.101.248')
            ftp.login('wdeployadmin', 'wdeployadmin')
            ftp.cwd(downloaddir)
            local_path = '/opt/tmp/' + appid + '/'
            os.system('mkdir %s -p' % local_path)
            localfile = local_path + version + '.zip'
            localmd5 = local_path + version + '.md5'
            file_handler = open(localfile, 'wb')
            ftp.retrbinary(u'RETR %s' % (file), file_handler.write)
            file_handler.close()
            md5_handler = open(localmd5, 'wb')
            ftp.retrbinary(u'RETR %s' % (md5file), md5_handler.write)
            md5_handler.close()
            result = 'retcode:\n0'
            if 'cfg' in appid:
                os.chdir(local_path)
                os.rename('%s.zip' % version, '%s.zip' % version_info)
                os.rename('%s.md5' % version, '%s.md5' % version_info)
            unpack(appid, taskid)
            return result
        except Exception, e:
            result = 'retcode:\n1\%s' % e
            return result
    else:
        result = 'retcode:\n1'
        return result


def get_configuration(typeid, appid, taskid):
    if typeid == 'iis':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'nodejs':
        all = appid.split('/')
        item = all[-2]
        version = all[-1]
        config_dir = 'configuration/' + all[1] + '/' + item + '/STAGING_PROD'
        try:
            file = 'latest.zip'
            md5file = 'latest.md5'
            ftp = FTP('10.10.101.248')
            ftp.login('config', '455b39d884ef14ec0006231928d1abdf')
            ftp.cwd(config_dir)
            local_path = '/opt/tmp/' + appid + '/'
            os.system('mkdir %s -p' % local_path)
            localfile = local_path + version + '.zip'
            localmd5 = local_path + version + '.md5'
            file_handler = open(localfile, 'wb')
            ftp.retrbinary(u'RETR %s' % (file), file_handler.write)
            file_handler.close()
            md5_handler = open(localmd5, 'wb')
            ftp.retrbinary(u'RETR %s' % (md5file), md5_handler.write)
            md5_handler.close()
            result = 'retcode:\n0'
            unpack(appid, taskid)
            config_path = '/usr/local/' + item + '/' + version + '/config.js'
            if os.path.isfile(config_path):
                modify(config_path)
            return result
        except Exception, e:
            result = 'retcode:\n1\n' + str(e)
            return result
    else:
        result = 'retcode:\n1'
        return result


def rollback(typeid, appid, taskid):
    if typeid == 'iis':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            stop_status = stop_app(node)
            if stop_status == 0:
                update_status = change_link(node, version)
                if update_status == 0:
                    start_status = start_app(node)
                    if start_status == 0:
                        result = 'retcode:\n0'
                        return result
                    else:
                        result = 'retcode:\n1\n start failed'
                        return result
                else:
                    result = 'retcode:\n1\n change link failed'
                    return result
            else:
                result = 'retcode:\n1\n stop failed'
                return result
        except:
            result = 'retcode:\n1'
            return result
    else:
        result = 'retcode:\n1'
        return result


def sync(typeid, appid, source):
    if typeid == 'iis':
        arguments = '-AppId {0} -Source {1}'.format(appid, source)
        output = __salt__['cmd.script']('salt://scripts/msdeploy.ps1', arguments, shell='powershell')
        return output
    elif typeid == 'handler':
        result = 'retcode:\n0'
        return result
    elif typeid == 'service':
        result = 'retcode:\n0'
        return result
    elif typeid == 'nodejs':
        os.system('mkdir -p /usr/local/%s' % appid)
        version = appid.split('/')[-1]
        node = appid.split('/')[-2]
        cmd = 'rsync -av %s::app/%s/ /usr/local/%s/' % (source, appid, appid)
        ret = os.system(cmd)
        if ret == 0:
            stop_status = stop_app(node)
            if stop_status == 0:
                update_status = change_link(node, version)
                if update_status == 0:
                    start_status = start_app(node)
                    if start_status == 0:
                        result = 'retcode:\n0'
                        return result
                    else:
                        result = 'retcode:\n1\n start failed'
                        return result
                else:
                    result = 'retcode:\n1\n change link failed'
                    return result
            else:
                result = 'retcode:\n1\n stop failed \n'
                return result
        else:
            result = 'retcode:\n1\nsync from %s error!' % source
            return result
    else:
        result = 'retcode:\n1'
        return result


def complete(typeid, appid, taskid):
    if typeid == 'iis':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Complete")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Complete")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Complete")
        return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')
    elif typeid == 'nodejs':
        result = 'retcode:\n0'
        return result
    else:
        result = 'retcode:\n1'
        return result
