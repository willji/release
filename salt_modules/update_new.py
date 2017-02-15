import re
import sys
import os
import logging
import zipfile
import datetime
import subprocess
from hashlib import md5
from ftplib import FTP
from logging.handlers import RotatingFileHandler


LOG_FILE = r'C:\salt\var\log\salt\update.log' if sys.platform == 'win32' else '/var/log/salt/update.log'
BACKUP_COUNT = 5
FORMAT = '%(asctime)s %(levelname)s %(module)s %(funcName)s-[%(lineno)d] %(message)s'
MAX_BYTES = 10 * 1024 * 1024

handler = RotatingFileHandler(LOG_FILE, mode='a', maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def command(cmd, shell='bash'):
    p = subprocess.Popen(args=[shell, '-l', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    pid = p.pid
    code = p.wait()
    out, err = p.communicate()
    logger.info("execute {0}, stdout is: {1} stderr is: {2}".format(cmd, out, err))
    return {"pid": pid, 'retcode': code, 'stderr': err, 'stdout': out}


def get_result(retcode, result):
    a = {}
    if retcode == 0:
        a['retcode'] = retcode
        a['stderr'] = ''
        a['stdout'] = result
    else:
        a['retcode'] = retcode
        a['stderr'] = result
        a['stdout'] = ''
    return a


def compress(dirname, zip_filename):
    try:
        file_list = []
        if os.path.isfile(dirname):
            file_list.append(dirname)
        else:
            for root, dirs, files in os.walk(dirname):
                for name in files:
                    file_list.append(os.path.join(root, name))
        zf = zipfile.ZipFile(zip_filename, "w", zipfile.zlib.DEFLATED)
        for tar in file_list:
            arc_name = tar[len(dirname):]
            zf.write(tar, arc_name)
        zf.close()
        return get_result(0, 'done')
    except Exception as e:
        logger.error('compress {0} to {1} error: {2}'.format(dirname, zip_filename, e))
        return get_result(1, str(e))


def md5sum(path):
    m = md5()
    try:
        with open(path) as fd:
            while True:
                block = fd.read(8096)
                if not block:
                    break
                m.update(block)
        return m.hexdigest()
    except Exception as e:
        logger.error("check sum of {0} error: {1}".format(path, e))
        return False


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
    try:
        f = zipfile.ZipFile(file, 'r')
        for m in f.namelist():
            f.extract(m, dir)
        return get_result(0, 'done')
    except Exception, e:
        return get_result(1, str(e))


def unpack(file, md5file, dir):
    f = open(md5file)
    content = f.read()
    f.close()
    newmd5 = content.split(' ')[0]
    md5value = md5sum(file)
    if newmd5 == md5value:
        result = extract(file, dir)
        return result
    else:
        return get_result(1, 'wrong md5 value')


def get_ftp(ftp_file, local_file, ftpid):
    try:
        ftp_info = ftpid.split(',')
        ftp_host = ftp_info[0]
        ftp_user = ftp_info[1]
        ftp_password = ftp_info[2]
        ftp = FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)
        ftp_path = '/'.join(ftp_file.split('/')[:-1])
        file = ftp_file.split('/')[-1]
        ftp.cwd(ftp_path)
        file_handler = open(local_file, 'wb')
        ftp.retrbinary(u'RETR %s' % (file), file_handler.write)
        file_handler.close()
        return get_result(0, 'done')
    except Exception, e:
        return get_result(1, str(e))


def upload_ftp(ftp_path, local_file, ftpid):
    try:
        ftp_info = ftpid.split(',')
        ftp_host = ftp_info[0]
        ftp_user = ftp_info[1]
        ftp_password = ftp_info[2]
        md5_value = md5sum(local_file)
        md5_file = re.sub('zip$', 'md5', local_file)
        ftp = FTP(ftp_host)
        ftp.login(ftp_user, ftp_password)
        ftp_path_info = ftp_path.split('/')
        for m in ftp_path_info:
            try:
                ftp.mkd(m)
                ftp.cwd(m)
            except:
                ftp.cwd(m)
        f = open(local_file, 'rb')
        ftp.storbinary('STOR %s' % os.path.basename(local_file), f)
        md5 = open(md5_file, 'rb')
        ftp.storbinary('STOR %s' % os.path.basename(md5_file), md5)
        return get_result(0, 'done')
    except Exception, e:
        return get_result(1, str(e))


def start_app(appid):
    if os.path.exists('/usr/local/deploy/%s/start.sh' % appid):
        return command('/usr/local/deploy/%s/start.sh' % appid, shell='su')
    else:
        return __salt__['script.run']('salt://scripts/deploy/%s/start.sh' % appid)


def stop_app(appid):
    if os.path.exists('/usr/local/deploy/%s/stop.sh' % appid):
        return command('/usr/local/deploy/%s/stop.sh' % appid, shell='su')
    else:
        return __salt__['script.run']('salt://scripts/deploy/%s/stop.sh' % appid)


def change_link(appid, version):
    os.chdir('/usr/local/%s' % appid)
    try:
        os.unlink('default')
        os.symlink(version, 'default')
        return {'retcode': 0, 'stderr': '', 'stdout': 'done'}
    except Exception as e:
        return {'retcode': 1, 'stderr': str(e), 'stdout': ''}


def new(type, appid, taskid):
    if type in ['iis','static_win']:
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(taskid, appid, "NewSite")
        if type == 'static_win':
            return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif type == 'service':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(taskid, appid, "NewService")
        return __salt__['cmd.script']('salt://scripts/publish_svc_latest.ps1', args=arguments, shell='powershell')
    elif type == 'handler':
        return {'retcode': 0, 'stdout': 'skip type handler', 'stderr': ''}
    elif type == 'static':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            ret = command('mkdir /usr/local/%s/default -p' % node)
            if ret.get('retcode') != 0:
                return ret
            os.chdir('/usr/local/%s' % node)
            return command('\cp -r {0}/. default'.format(version))
        except Exception as e:
            logger.error("execute task new args type: {0} appid: {1} taskid: {2} error: {3}".format(type, appid,
                                                                                                    taskid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    elif type == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            ret = command('mkdir /usr/local/%s -p' % node)
            if ret.get('retcode', 1) != 0:
                return ret
            os.chdir('/usr/local/%s' % node)
            ret = command('ln -s %s default' % version)
            if ret.get('retcode', 1) != 0:
                return ret
            return start_app(node)
        except Exception as e:
            logger.error("execute task new args type: {0} appid: {1} taskid: {2} error: {3}".format(type, appid,
                                                                                                    taskid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def update(typeid, appid, ftpid):
    if typeid in ['iis','static_win']:
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "UpdateSite")
        if typeid == 'static_win':
            return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "UpdateService")
        return __salt__['cmd.script']('salt://scripts/publish_svc_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        return {'retcode': 0, 'stdout': 'skip type handler', 'stderr': ''}
    elif typeid == 'static':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            os.chdir('/usr/local/%s' % node)
            return command('\cp -r {0}/. default'.format(version))
        except Exception as e:
            logger.error("execute task update args type: {0} appid: {1} ftpid: {2} error: {3}".format(typeid, appid,
                                                                                                      ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    elif typeid == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            os.chdir('/usr/local/%s' % node)
            ret = stop_app(node)
            if ret.get('retcode', 1) != 0:
                return ret
            ret = change_link(node, version)
            if ret.get('retcode', 1) != 0:
                return ret
            return start_app(node)
        except Exception as e:
            logger.error("execute task update args type: {0} appid: {1} ftpid: {2} error: {3}".format(typeid, appid,
                                                                                                      ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def get_package(typeid, appid, ftpid):
    if typeid in ['iis','static_win']:
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_svc_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetFtpPackage")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid in ['nodejs', 'static']:
        try:
            all = appid.split('/')
            dep = all[1]
            item = all[2]
            version = all[-1]
            if 'cfg' in version.lower():
                version_to_download = version.split('_')[0]
            else:
                version_to_download = version
            package_file = 'production/%s/%s/%s/%s.zip' % (dep, item, version_to_download, version_to_download)
            package_md5 = 'production/%s/%s/%s/%s.md5' % (dep, item, version_to_download, version_to_download)
            local_tmp_file = '/opt/tmp/package/%s/%s/%s/%s.zip' % (dep, item, version_to_download, version_to_download)
            local_tmp_md5 = '/opt/tmp/package/%s/%s/%s/%s.md5' % (dep, item, version_to_download, version_to_download)
            local_tmp_dir = '/opt/tmp/package/%s/%s/%s/' % (dep, item, version_to_download)
            ret = command('/bin/mkdir -p %s' % local_tmp_dir)
            if ret.get('retcode', 1) != 0:
                return ret
            ret = get_ftp(package_file, local_tmp_file, ftpid)
            if ret.get('retcode', 1) != 0:
                return ret
            ret = get_ftp(package_md5, local_tmp_md5, ftpid)
            if ret.get('retcode', 1) != 0:
                return ret
            unpack_dir = '/usr/local/%s/%s' % (item, version)
            ret = command('/bin/mkdir -p %s' % unpack_dir)
            if ret.get('retcode', 1) != 0:
                return ret
            unpack_result = unpack(local_tmp_file, local_tmp_md5, unpack_dir)
            return unpack_result
        except Exception as e:
            logger.error("execute task get_package args type: {0} appid: {1} ftpid: {2} error: {3}".format(typeid, appid,
                                                                                                           ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def get_configuration(typeid, appid, ftpid, env='STAGING_PROD'):
    if typeid in ['iis', 'static_win']:
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_svc_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(ftpid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid in ['nodejs','static']:
        try:
            all = appid.split('/')
            dep = all[1]
            item = all[2]
            version = all[-1]
            package_file = 'configuration/%s/%s/%s/latest.zip' % (dep, item, env)
            package_md5 = 'configuration/%s/%s/%s/latest.md5' % (dep, item, env)
            local_tmp_dir = '/opt/tmp/configuration/%s/%s/%s/%s' % (dep, item, version, env)
            local_tmp_file = '%s/%s.zip' % (local_tmp_dir, version)
            local_tmp_md5 = '%s/%s.md5' % (local_tmp_dir, version)
            ret = command('/bin/mkdir -p %s' % local_tmp_dir)
            if ret.get('retcode') != 0:
                return ret
            ret = get_ftp(package_file, local_tmp_file, ftpid)
            if ret.get('retcode') != 0:
                return ret

            ret = get_ftp(package_md5, local_tmp_md5, ftpid)
            if ret.get('retcode') != 0:
                return ret
            unpack_dir = '/usr/local/%s/%s' % (item, version)
            ret = command('/bin/mkdir -p %s' % unpack_dir)
            if ret.get('retcode') != 0:
                return ret
            ret = unpack(local_tmp_file, local_tmp_md5, unpack_dir)
            if ret.get('retcode') != 0:
                return ret
            config_path = '/usr/local/' + item + '/' + version + '/config.js'
            if os.path.isfile(config_path):
                modify(config_path)
            return ret
        except Exception as e:
            logger.error("execute task get_configuration args type: {0} appid: {1} ftpid: {2} error: {3}"
                         .format(typeid, appid, ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def get_production(typeid, appid, ftpid):
    if typeid in ['iis','static_win']:
        arguments = "-FTP {0} -AppId {1}".format(ftpid, appid)
        return __salt__['cmd.script']('salt://scripts/msdeploy_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-FTP {0} -AppId {1}".format(ftpid, appid)
        return __salt__['cmd.script']('salt://scripts/publish_svc_v2.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-FTP {0} -AppId {1}".format(ftpid, appid)
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid in ['nodejs', 'static']:
        try:
            all = appid.split('/')
            dep = all[-3]
            item = all[-2]
            version = all[-1]
            package_file = 'production/%s/%s/%s/%s_%s.zip' % (dep, item, version, item, version)
            package_md5 = 'production/%s/%s/%s/%s_%s.md5' % (dep, item, version, item, version)
            local_tmp_file = '/opt/tmp/production/%s/%s/%s/%s.zip' % (dep, item, version, version)
            local_tmp_md5 = '/opt/tmp/production/%s/%s/%s/%s.md5' % (dep, item, version, version)
            local_tmp_dir = '/opt/tmp/production/%s/%s/%s' % (dep, item, version)
            ret = command('/bin/mkdir -p %s' % local_tmp_dir)
            if ret.get('retcode') != 0:
                return ret
            ret = get_ftp(package_file, local_tmp_file, ftpid)
            if ret.get('retcode') != 0:
                return ret
            ret = get_ftp(package_md5, local_tmp_md5, ftpid)
            if ret.get('retcode') != 0:
                return ret
            unpack_dir = '/usr/local/%s/%s' % (item, version)
            ret = command('/bin/mkdir -p %s' % unpack_dir)
            if ret.get('retcode') != 0:
                return ret
            ret = unpack(local_tmp_file, local_tmp_md5, unpack_dir)
            if ret.get('retcode') != 0:
                return ret
            return update(typeid, appid, ftpid)
        except Exception as e:
            logger.error("execute task get_production args type: {0} appid: {1} ftpid: {2} error: {3}"
                         .format(typeid, appid, ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def upload(typeid, appid, ftpid):
    """upload the config zip"""
    if typeid in ['iis', 'static_win']:
        arguments = "-FTP {0} -AppId {1}".format(ftpid, appid)
        return __salt__['cmd.script']('salt://scripts/package_site.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        return get_result(0, 'service no need upload')
    elif typeid == 'handler':
        return get_result(0, 'handler no need upload')
    elif typeid in ['nodejs', 'static']:
        try:
            all = appid.split('/')
            dep = all[0]
            item = all[1]
            version = all[2]
            upload_dir = 'production/%s/%s/%s' % (dep, item, version)
            compress_path = '/usr/local/%s/%s' % (item, version)
            zip_file = '/opt/tmp/production/%s/%s/%s/%s_%s.zip' % (dep, item, version, item, version)
            zip_dir = '/opt/tmp/production/%s/%s/%s' % (dep, item, version)
            logger.info(upload_dir)
            logger.info(compress_path)
            logger.info(zip_file)
            logger.info(zip_dir)
            ret = command('/bin/mkdir -p %s' % zip_dir)
            if ret.get('retcode') != 0:
                return ret
            md5_file = re.sub('zip$', 'md5', zip_file)
            ret = command('/bin/rm %s -f' % zip_file)
            if ret.get('retcode') != 0:
                return ret
            ret = command('/bin/rm %s -f' % md5_file)
            if ret.get('retcode') != 0:
                return ret
            ret = compress(compress_path, zip_file)
            if ret.get('retcode') != 0:
                return ret
            md5_value = md5sum(zip_file)
            os.mknod(md5_file)
            with open(md5_file, 'w') as file:
                file.write(md5_value)
            return upload_ftp(upload_dir, zip_file, ftpid)
        except Exception as e:
            logger.error("execute task upload args type: {0} appid: {1} ftpid: {2} error: {3}"
                         .format(typeid, appid, ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def rollback(typeid, appid, taskid):
    if typeid == 'iis':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
        return __salt__['cmd.script']('salt://scripts/publish_svc_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-FTP {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'nodejs':
        try:
            version = appid.split('/')[-1]
            node = appid.split('/')[-2]
            ret = stop_app(node)
            if ret.get('retcode') != 0:
                return ret
            ret = change_link(node, version)
            if ret.get('retcode') != 0:
                return ret
            return start_app(node)
        except Exception as e:
            logger.error("execute task rollback args type: {0} appid: {1} taskid: {2} error: {3}"
                         .format(typeid, appid, taskid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}


def complete(typeid, appid, ftpid):
    if typeid in ['iis', 'static_win']:
        arguments = "-AppId {0} -Step {1} -Ftp {2}".format(appid, "Complete", ftpid)
        return __salt__['cmd.script']('salt://scripts/publish_latest.ps1', args=arguments, shell='powershell')
    elif typeid == 'handler':
        arguments = "-AppId {0} -Step {1} -Ftp {2}".format(appid, "Complete", ftpid)
        return __salt__['cmd.script']('salt://scripts/publish_handler.ps1', args=arguments, shell='powershell')
    elif typeid == 'service':
        arguments = "-AppId {0} -Step {1} -Ftp {2}".format(appid, "Complete", ftpid)
        return __salt__['cmd.script']('salt://scripts/publish_svc_latest.ps1', args=arguments, shell='powershell')
    elif typeid in ['nodejs','static']:
        try:
            item = appid.split('/')[-2]
            os.chdir('/usr/local/%s' % item)
            if typeid == 'static':
                ret = command("ls -t | grep -v default | head -n 1")
            else:
                ret = command("ls -l | grep default | awk '{print $NF}'")
            if ret.get('retcode') == 0:
                ret['stdout'] = ret.get('stdout', '').strip()
            return ret
        except Exception as e:
            logger.error("execute task rollback args type: {0} appid: {1} ftpid: {2} error: {3}"
                         .format(typeid, appid, ftpid, e))
            return {'retcode': 1, 'stdout': '', 'stderr': str(e)}
    else:
        return {'retcode': 1, 'stdout': '', 'stderr': 'unknown type {0}'.format(type)}
