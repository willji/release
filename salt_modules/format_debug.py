data = (u'service', u'production/infra/deliveryservice/T78063', u'10.10.101.248,wdeployadmin,wdeployadmin')

print [str(x) for x in data]
shell = 'C:\\salt\\var\\cache\\salt\\minion\\files\\base\\scripts\\publish_svc_latest.ps1'

print '%s -FTP %s -AppId %s -Step %s' % (shell, data[2],data[1],data[0])

