import os
import platform
def ops_check(appid, taskid):
    plat = platform.system()
    if (plat == "Windows"):
        arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "OpsCheck")
        return __salt__['cmd.script']('salt://scripts/publish_v2.ps1', args=arguments, shell='powershell')
    else:
        try:
            item=appid.split('/')[-2]
            os.chdir('/usr/local/%s' %item)
            result=os.popen("ls -l | grep default | awk '{print $NF}'")
            current_version=result.read().strip()
            all={}
            all['retcode']=0
            all['stderr']=''
            all['stdout']=current_version
            return all
        except Exception,e:
            all={}
            all['retcode']=1
            all['stderr']=e
            all['stdout']=''
            return all
            
 
