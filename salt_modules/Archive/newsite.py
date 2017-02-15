def get_package(appid, taskid):
    '''
    Instruct the minion to get package by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.get_package 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetPackage")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')

def get_configuration(appid, taskid):
    '''
    Instruct the minion to get configuration by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.get_configuration 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "GetConfiguration")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')

def new_site(appid, taskid):
    '''
    Instruct the minion to get configuration by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.new_site 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "NewSite")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')

def rollback_site(appid, taskid):
    '''
    Instruct the minion to update site by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.rollback_site 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Rollback")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')

def ops_check(appid, taskid):
    '''
    Instruct the minion to update site by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.ops_check 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "OpsCheck")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')

def complete(appid, taskid):
    '''
    Instruct the minion to update site by appid.

    CLI Example:

    .. code-block:: bash

        salt '*' publish.complete 'api.app.ymatou.com' taskid
    '''
    
    arguments = "-TaskId {0} -AppId {1} -Step {2}".format(taskid, appid, "Complete")
    return __salt__['cmd.script']('salt://scripts/publish.ps1', args=arguments, shell='powershell')