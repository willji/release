import os
import sys
import shutil
import zipfile
import tempfile
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


def _nssm_install():
    if os.path.exists('d:\\nssm'):
        return {'retcode': 0, 'stdout': 'nssm exist', 'stderr': '', 'pid': 0}
    dest = tempfile.mkdtemp()
    __salt__['cp.get_file']('salt://packages/nssm.zip', '{0}\\nssm.zip'.format(dest))
    os.chdir('d:')
    z = None
    try:
        z = zipfile.ZipFile('{0}\\nssm.zip'.format(dest))
        z.extractall()
        return {'retcode': 0, 'stderr': '', 'stdout': 'done'}
    except Exception as e:
        return {'retcode': '-1', 'stderr': str(e), 'stdout': ''}
    finally:
        if z is not None:
            z.close()
        shutil.rmtree(dest)


def _nssm_uninstall():
    if not os.path.exists('d:\\nssm'):
        return {'retcode': 0, 'stdout': 'nssm not exist', 'stderr': '', 'pid': 0}
    return __salt__['cmd.script']('salt://packages/nssm/uninstall.ps1', shell='powershell')


def _install_daemontools():
    dest = tempfile.mkdtemp()
    __salt__['cp.get_file']('salt://packages/daemontools-0.76-1.el6.x86_64.rpm',
                            '{0}/daemontools-0.76-1.el6.x86_64.rpm'.format(dest))
    try:
        return _command('rpm -Uvh {0}/daemontools-0.76-1.el6.x86_64.rpm'.format(dest))
    finally:
        shutil.rmtree(dest)


def _start_daemontools():
    return _command('initctl start daemontools')


def _stop_daemontools():
    return _command('initctl stop daemontools')


def _restart_daemontools():
    return _command('initctl restart daemontools')


def _uninstall_daemontools():
    return _command('initctl stop daemontools; rpm -e daemontools')


def _action(action):
    return __salt__['cmd.script']('salt://packages/nssm/{0}.ps1'.format(action), shell='powershell')


def install():
    if _is_windows():
        return _nssm_install()
    return _install_daemontools()


def uninstall():
    if _is_windows():
        return _nssm_uninstall()
    return _uninstall_daemontools()


def start():
    if _is_windows():
        return _action('start')
    return _start_daemontools()


def stop():
    if _is_windows():
        return _action('stop')
    return _stop_daemontools()


def restart():
    if _is_windows():
        return _action('restart')
    return _restart_daemontools()

