import os
from os.path import getsize

test_path = 'd:\\logfiles'
import platform
import time
import re


# for i in range(100):
#     os.mkdir('%s\\%s' % (test_path, str(i)))

# for i in range(100):
#     file_object = open('%s\\%s\\thefile%s.txt' % (test_path, str(i), str(i)), 'w')
#     file_object.write('test'+str(i))
#     file_object.close()
def getfiles(dirpath):
    a = [s for s in os.listdir(dirpath)
         if os.path.isfile(os.path.join(dirpath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)))
    return a


print getfiles(test_path)
