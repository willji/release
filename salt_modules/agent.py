import os
import sys
import shutil
import tempfile
import zipfile
import subprocess


def _is_windows():
    return sys.platform == 'win32'


def _command(cmd):
    args = ['powershell.exe', '-ExecutionPolicy', 'Unrestricted', '-File', cmd] if _is_windows() \
        else ['bash', '-l', '-c', cmd]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    pid = p.pid
    code = p.wait()
    out, err = p.communicate()
    return {"pid": pid, 'retcode': code, 'stderr': err, 'stdout': out}


def install(name):
    dest = tempfile.mkdtemp()
    filename = 'windows.zip' if _is_windows() else 'linux.zip'
    __salt__['cp.get_file']('salt://packages/{0}/{1}'.format(name, filename), '{0}/{1}'.format(dest, filename))
    os.chdir(dest)
    z = None
    try:
        z = zipfile.ZipFile(filename)
        z.extractall()
        if _is_windows():
            os.chdir('{0}_windows'.format(name))
        else:
            os.chdir('{0}_linux'.format(name))
        cmd = '.\\install.ps1' if _is_windows() else 'sh ./install.sh'
        return _command(cmd)
    except Exception as e:
        return {'retcode': '-1', 'stderr': str(e), 'stdout': ''}
    finally:
        if z is not None:
            z.close()
        os.chdir('/')
        shutil.rmtree(dest)


def uninstall(name):
    dest = tempfile.mkdtemp()
    filename = 'windows.zip' if _is_windows() else 'linux.zip'
    __salt__['cp.get_file']('salt://packages/{0}/{1}'.format(name, filename), '{0}/{1}'.format(dest, filename))
    os.chdir(dest)
    z = None
    try:
        z = zipfile.ZipFile(filename)
        z.extractall()
        if _is_windows():
            os.chdir('{0}_windows'.format(name))
        else:
            os.chdir('{0}_linux'.format(name))
        cmd = '.\\uninstall.ps1' if _is_windows() else 'sh ./uninstall.sh'
        return _command(cmd)
    except Exception as e:
        return {'retcode': '-1', 'stderr': str(e), 'stdout': ''}
    finally:
        if z is not None:
            z.close()
        os.chdir('/')
        shutil.rmtree(dest)


def _action(name, action):
    cmd = ''
    try:
        if _is_windows():
            os.chdir('d:\\agents\\{0}'.format(name))
            cmd = '.\\bin\\{0}.ps1'.format(action)
        else:
            os.chdir('/opt/agents/{0}'.format(name))
            cmd = './bin/{0}.sh'.format(action)
        return _command(cmd)
    finally:
        os.chdir('/')


def stop(name):
    return _action(name, 'stop')


def start(name):
    return _action(name, 'start')


def restart(name):
    return _action(name, 'restart')
