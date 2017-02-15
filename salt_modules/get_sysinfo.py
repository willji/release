# -*- coding:utf-8 -*-
# __author__='guziqiang'
# __create_time__ = '2016/12/27'
import os
import subprocess

def command(cmd, shell='bash'):
    p = subprocess.Popen(args=[shell, '-l', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    pid = p.pid
    code = p.wait()
    out, err = p.communicate()
    return {"pid": pid, 'retcode': code, 'stderr': err, 'stdout': out}

def get_uptime():
    if os.name == 'nt':
        return __salt__['cmd.script']('salt://scripts/Get-UpTime.ps1', shell='powershell')
    else:
        cmd = 'date -d "$(awk -F. \'{print $1}\' /proc/uptime) second ago" +"%Y-%m-%d %H:%M:%S"'
        result = command(cmd)
        return result

def do_script():
    if os.name == 'nt':
        return __salt__['cmd.script']('salt://scripts/cmd_run.ps1', shell='powershell')
    else:
        pass
