import re
import datetime
import zipfile
from ftplib import FTP
import os
import md5

SCRIPT_STOP_SH = '/usr/local/deploy/%s/stop.sh'
SCRIPT_START_SH = '/usr/local/deploy/%s/start.sh'
Script_Publish = 'publish_latest.ps1'
Script_Publish_Service = 'publish_svc_latest.ps1'
Script_Publish_Handler = 'publish_handler_latest.ps1'
Script_Publish_Msdeploy = 'msdeploy_latest.ps1'
Script_Publish_PackageSite = 'package_site.ps1'


class PublishStep(object):
    Complete = 'Complete'
    Rollback = 'Rollback'
    GetConfiguration = 'GetConfiguration'
    GetFtpPackage = 'GetFtpPackage'
    UpdateSite = 'UpdateSite'
    UpdateService = 'UpdateService'
    NewSite = 'NewSite'
    NewService = 'NewService'


class PublishType(object):
    IIS = 'iis'
    Handler = 'handler'
    Service = 'service'
    Nodejs = 'nodejs'
    Java = 'java'
    Nginx = 'nginx'


def try_except(func):
    def wrapped(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except Exception, e:
            result = get_result(1, str(e))
        finally:
            return result

    return wrapped


def get_result(retcode, result):
    if retcode == 0:
        return {'retcode': retcode, 'stderr': '', 'stdout': result}
    else:
        return {'retcode': retcode, 'stderr': result, 'stdout': ''}


class PublishBase(object):
    script_iis = Script_Publish
    script_service = Script_Publish_Service
    script_handler = Script_Publish_Handler
    step_iis, step_service, step_handler = None, None, None
    unzip = False

    def __init__(self, typeid, appid, ftpid):
        self.typeid = typeid
        self.appid = appid
        self.ftpid = ftpid

    def __format_args(self, stepid):
        if stepid:
            return "-FTP {0} -AppId {1} -Step {2}".format(self.ftpid, self.appid, stepid)
        else:
            return "-FTP {0} -AppId {1}".format(self.ftpid, self.appid)

    def salt_script(self, script_name, stepid, *args, **kwargs):
        if self.unzip:
            __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
        return __salt__['cmd.script']('salt://scripts/%s' % script_name, shell='powershell', args=self.__format_args(stepid), *args, **kwargs)

    def run(self):
        if self.typeid == PublishType.IIS:
            return self.run_iis()
        elif self.typeid == PublishType.Service:
            return self.run_service()
        elif self.typeid == PublishType.Handler:
            return self.run_handler()
        elif self.typeid == PublishType.Nodejs or self.typeid == PublishType.Java:
            return self.run_nodejs()
        else:
            return get_result(1, 'no this type %s' % self.typeid)

    def run_iis(self):
        return self.salt_script(self.script_iis, self.step_iis)

    def run_service(self):
        return self.salt_script(self.script_service, self.step_service)

    def run_handler(self):
        return self.salt_script(self.script_handler, self.step_handler)

    def run_nodejs(self):
        pass


class PublishNew(PublishBase):
    step_iis = PublishStep.NewSite
    step_service = PublishStep.NewService

    def run_handler(self):
        return get_result(1, 'not support create handler')

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).new()


class PublishUpdate(PublishBase):
    step_iis = PublishStep.UpdateSite
    step_service = PublishStep.UpdateService

    def run_handler(self):
        return get_result(1, 'not support update handler ')

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).update()


class PublishGetPackage(PublishBase):
    step_iis = PublishStep.GetFtpPackage
    step_service = PublishStep.GetFtpPackage
    step_handler = PublishStep.GetFtpPackage
    unzip = True

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).get_package()


class PublishGetConfiguration(PublishBase):
    step_iis = PublishStep.GetConfiguration
    step_service = PublishStep.GetConfiguration
    step_handler = PublishStep.GetConfiguration

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).get_configuration()


class PublishGetProduction(PublishBase):
    script_iis = Script_Publish_Msdeploy

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).get_production()


class PublishUpload(PublishBase):
    script_iis = Script_Publish_PackageSite

    def run_service(self):
        return get_result(1, 'not support service upload')

    def run_handler(self):
        return get_result(1, 'not support handler upload')

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).upload()


class PublishComplete(PublishBase):
    step_iis = PublishStep.Complete
    step_service = PublishStep.Complete
    step_handler = PublishStep.Complete

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).complete()


class PublishRollBack(PublishBase):
    step_iis = PublishStep.Rollback
    step_service = PublishStep.Rollback
    step_handler = PublishStep.GetConfiguration

    def run_nodejs(self):
        return PublishNodeJs(self.appid, self.ftpid).rollback()


def new(typeid, appid, ftpid):
    return PublishNew(typeid, appid, ftpid).run()


def update(typeid, appid, ftpid):
    return PublishUpdate(typeid, appid, ftpid).run()


def get_package(typeid, appid, ftpid):
    return PublishGetPackage(typeid, appid, ftpid).run()


def get_configuration(typeid, appid, ftpid):
    return PublishGetConfiguration(typeid, appid, ftpid).run()


def get_production(typeid, appid, ftpid):
    return PublishGetProduction(typeid, appid, ftpid).run()


def upload(typeid, appid, ftpid):
    return PublishUpload(typeid, appid, ftpid).run()


def complete(typeid, appid, ftpid):
    return PublishComplete(typeid, appid, ftpid).run()


def rollback(typeid, appid, ftpid):
    return PublishRollBack(typeid, appid, ftpid).run()


class PublishLinux(object):
    @staticmethod
    @try_except
    def compress(dir_name, zip_filename):
        file_list = []
        if os.path.isfile(dir_name):
            file_list.append(dir_name)
        else:
            for root, dirs, files in os.walk(dir_name):
                for name in files:
                    file_list.append(os.path.join(root, name))
        zf = zipfile.ZipFile(zip_filename, "w", zipfile.zlib.DEFLATED)
        for tar in file_list:
            zf.write(tar, tar[len(dir_name):])
        zf.close()
        return get_result(0, 'done')

    @staticmethod
    def sum_file(f_obj):
        m = md5.new()
        while True:
            d = f_obj.read(8096)
            if not d:
                break
            m.update(d)
        return m.hexdigest()

    def md5sum(self, f_name):
        try:
            f = file(f_name, 'rb')
        except:
            return False
        ret = self.sum_file(f)
        f.close()
        return ret

    @staticmethod
    def modify(file_path):
        new_version = datetime.datetime.now().strftime("%y%m%d%H%M")
        fp = open(file_path, 'r')
        all_lines = fp.readlines()
        fp.close()
        fp = open(file_path, 'w')
        for each_line in all_lines:
            a = re.sub('new_version', new_version, each_line)
            fp.writelines(a)
        fp.close()

    @staticmethod
    @try_except
    def extract(file_path, dir_path):
        f = zipfile.ZipFile(file_path, 'r')
        for m in f.namelist():
            f.extract(m, dir_path)
        return get_result(0, 'done')

    def unpack(self, file_path, md5file, dir_path):
        f = open(md5file)
        content = f.read()
        f.close()
        new_md5 = content.split(' ')[0]
        md5value = self.md5sum(file_path)
        if new_md5 == md5value:
            return self.extract(file_path, dir_path)
        else:
            return get_result(1, 'wrong md5 value')

    @staticmethod
    @try_except
    def get_ftp(ftp_file, local_file, ftp_id):
        ftp_info = ftp_id.split(',')
        ftp = FTP(ftp_info[0])
        ftp.login(ftp_info[1], ftp_info[2])
        ftp_path = '/'.join(ftp_file.split('/')[:-1])
        file_name = ftp_file.split('/')[-1]
        ftp.cwd(ftp_path)
        file_handler = open(local_file, 'wb')
        ftp.retrbinary(u'RETR %s' % file_name, file_handler.write)
        file_handler.close()
        return get_result(0, 'done')

    @try_except
    def upload_ftp(self, ftp_path, local_file, ftpid):
        ftp_info = ftpid.split(',')
        md5_value = self.md5sum(local_file)
        md5_file = re.sub('zip$', 'md5', local_file)
        ftp = FTP(ftp_info[0])
        ftp.login(ftp_info[1], ftp_info[2])
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

    @staticmethod
    def start_app(app_id):
        return os.system(SCRIPT_START_SH % app_id)

    @staticmethod
    def stop_app(app_id):
        return os.system(SCRIPT_STOP_SH % app_id)

    @staticmethod
    def change_link(app_id, version):
        os.chdir('/usr/local/%s' % app_id)
        return os.system('rm default -f && ln -s %s default' % version)


class PublishNodeJs(PublishLinux):
    def __init__(self, appid, ftpid):
        self.appid = appid
        self.ftpid = ftpid
        app = self.appid.split('/')
        self.version = app[-1]
        self.node = app[-2]
        self.dep = app[1]
        self.item = app[2]

    @try_except
    def new(self):
        os.system('mkdir /usr/local/%s -p' % self.node)
        os.chdir('/usr/local/%s' % self.node)
        os.system('ln -s %s default' % self.version)
        self.start_app(self.node)
        return get_result(0, 'done')

    @try_except
    def update(self):
        os.chdir('/usr/local/%s' % self.node)
        return self.__stop_change_link_start()

    def __down_and_unpack_file(self, local_tmp_dir, local_tmp_file, local_tmp_md5, package_file, package_md5):
        os.system('/bin/mkdir -p %s' % local_tmp_dir)
        file_result = self.get_ftp(package_file, local_tmp_file, self.ftpid)
        if file_result['retcode'] == 0:
            md5_result = self.get_ftp(package_md5, local_tmp_md5, self.ftpid)
            if md5_result['retcode'] == 0:
                pass
            else:
                return md5_result
        else:
            return file_result
        unpack_dir = '/usr/local/%s/%s' % (self.item, self.version)
        os.system('/bin/mkdir -p %s' % unpack_dir)
        return self.unpack(local_tmp_file, local_tmp_md5, unpack_dir)

    @try_except
    def get_package(self):
        if 'cfg' in self.version.lower():
            version_to_download = self.version.split('_')[0]
        else:
            version_to_download = self.version
        package_file = 'production/%s/%s/%s/%s.zip' % (self.dep, self.item, version_to_download, version_to_download)
        package_md5 = 'production/%s/%s/%s/%s.md5' % (self.dep, self.item, version_to_download, version_to_download)
        local_tmp_file = '/opt/tmp/package/%s/%s/%s/%s.zip' % (self.dep, self.item, version_to_download, version_to_download)
        local_tmp_md5 = '/opt/tmp/package/%s/%s/%s/%s.md5' % (self.dep, self.item, version_to_download, version_to_download)
        local_tmp_dir = '/opt/tmp/package/%s/%s/%s/' % (self.dep, self.item, version_to_download)
        return self.__down_and_unpack_file(local_tmp_dir, local_tmp_file, local_tmp_md5, package_file, package_md5)

    @try_except
    def get_configuration(self):
        package_file = 'configuration/%s/%s/STAGING_PROD/latest.zip' % (self.dep, self.item)
        package_md5 = 'configuration/%s/%s/STAGING_PROD/latest.md5' % (self.dep, self.item)
        local_tmp_file = '/opt/tmp/configuration/%s/%s/%s/%s.zip' % (self.dep, self.item, self.version, self.version)
        local_tmp_md5 = '/opt/tmp/configuration/%s/%s/%s/%s.md5' % (self.dep, self.item, self.version, self.version)
        local_tmp_dir = '/opt/tmp/configuration/%s/%s/%s' % (self.dep, self.item, self.version)
        return self.__down_and_unpack_file(local_tmp_dir, local_tmp_file, local_tmp_md5, package_file, package_md5)

    @try_except
    def get_production(self):
        package_file = 'production/%s/%s/%s/%s_%s.zip' % (self.dep, self.item, self.version, self.item, self.version)
        package_md5 = 'production/%s/%s/%s/%s_%s.md5' % (self.dep, self.item, self.version, self.item, self.version)
        local_tmp_file = '/opt/tmp/production/%s/%s/%s/%s.zip' % (self.dep, self.item, self.version, self.version)
        local_tmp_md5 = '/opt/tmp/production/%s/%s/%s/%s.md5' % (self.dep, self.item, self.version, self.version)
        local_tmp_dir = '/opt/tmp/production/%s/%s/%s' % (self.dep, self.item, self.version)
        unpack_result = self.__down_and_unpack_file(local_tmp_dir, local_tmp_file, local_tmp_md5, package_file, package_md5)
        if unpack_result['retcode'] == 0:
            return update('nodejs', self.appid, self.ftpid)
        else:
            return unpack_result

    @try_except
    def upload(self):
        upload_dir = 'production/%s/%s/%s' % (self.dep, self.item, self.version)
        compress_path = '/usr/local/%s/%s' % (self.item, self.version)
        zip_file = '/opt/tmp/production/%s/%s/%s/%s_%s.zip' % (self.dep, self.item, self.version, self.item, self.version)
        zip_dir = '/opt/tmp/production/%s/%s/%s' % (self.dep, self.item, self.version)
        os.system('/bin/mkdir -p %s' % zip_dir)
        md5_file = re.sub('zip$', 'md5', zip_file)
        os.system('/bin/rm %s -f' % zip_file)
        os.system('/bin/rm %s -f' % md5_file)
        zip_result = self.compress(compress_path, zip_file)
        if zip_result['retcode'] == 0:
            md5_value = self.md5sum(zip_file)
            os.mknod(md5_file)
            file = open(md5_file, 'w')
            file.write(md5_value)
            file.close()
            return self.upload_ftp(upload_dir, zip_file, self.ftpid)
        else:
            return zip_result

    @try_except
    def rollback(self):
        return self.__stop_change_link_start()

    def __stop_change_link_start(self):
        if self.stop_app(self.node) == 0:
            if self.change_link(self.node, self.version) == 0:
                if self.start_app(self.node) == 0:
                    result = get_result(0, 'done')
                else:
                    result = get_result(1, 'start failed')
            else:
                result = get_result(1, 'change link failed')
        else:
            result = get_result(1, 'stop failed')
        return result

    @try_except
    def complete(self):
        os.chdir('/usr/local/%s' % self.node)
        result = os.popen("ls -l | grep default | awk '{print $NF}'")
        return get_result(0, result.read().strip())


class PublishJava(PublishNodeJs):
    pass

