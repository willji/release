import os
import sys
import tempfile
import subprocess
import logging
from logging.handlers import RotatingFileHandler


LOG_FILE = r'C:\salt\var\log\salt\script.log' if sys.platform == 'win32' else '/var/log/salt/script.log'
BACKUP_COUNT = 5
FORMAT = '%(asctime)s %(levelname)s %(module)s %(funcName)s-[%(lineno)d] %(message)s'
MAX_BYTES = 10 * 1024 * 1024

handler = RotatingFileHandler(LOG_FILE, mode='a', maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT)
formatter = logging.Formatter(FORMAT)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def run(file, args=None):
    if sys.platform == 'win32':
        return {'pid': 0, 'retcode': -1, 'stderr': 'not support win32', 'stdout': ''}
    dest = tempfile.mktemp()
    __salt__['cp.get_file'](file, dest)
    os.chmod(dest, 0o755)
    if isinstance(args, (list, tuple)):
        args = ' '.join(args)
    if isinstance(args, str):
        cmd = '{0} {1}'.format(dest, args)
    else:
        cmd = dest
    p = subprocess.Popen(['su', '-l', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1)
    pid = p.pid
    code = p.wait()
    out, err = p.communicate()
    logger.info("execute script {0}, args:{1} retcode: {2} stdout: {3} stderr: {4}".format(file, args, code, out, err))
    return {'pid': pid, 'retcode': code, 'stderr': err, 'stdout': out}
