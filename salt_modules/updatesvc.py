def get_package(appid, taskid):
    __salt__['cp.get_file']('salt://scripts/unzip.exe', r'c:\windows\temp\unzip.exe')
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetFtpPackage")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')

def get_configuration(appid, taskid):
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')

def update(appid, taskid):
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "UpdateService")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')

def rollback(appid, taskid):
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')

def ops_check(appid, taskid):
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "OpsCheck")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')

def complete(appid, taskid):
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Complete")
    return __salt__['cmd.script']('salt://scripts/publish_svc.ps1', args=arguments, shell='powershell')