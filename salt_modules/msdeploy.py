def sync_wdsite(appid, source):
    arguments = '-AppId {0} -Source {1}'.format(appid, source)
    output = __salt__['cmd.script']('salt://scripts/msdeploy.ps1', arguments, shell='powershell')
    return output