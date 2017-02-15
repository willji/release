from core.common import get_result, logger, EXEC_NAME, STATUS_LIST, try_except, ReleaseEnv, ReleaseStatus, ReleaseError, ExecName, ReleaseStep, ReleaseType
from release.models import Status, Type_step, Type, Progress, Mission_control, Mission
from release_action.api import CmdbApi
from django.db.models import Q
from ftplib import FTP
import commands
import datetime


class MissionAct(object):
    mission_id = None
    expand = False

    def __init__(self, item, version, env=None, creator='anonymous', mock_data=None):
        self.item = item
        self.version = version
        self.env = env
        self.creator = creator
        self.mock_data = mock_data

    def __get_item_and_version(self):
        if self.mock_data and isinstance(self.mock_data, tuple):
            self.item_result = self.mock_data[0]
            self.version_result = self.mock_data[1]
        else:
            api = CmdbApi()
            item_path = '/api/cmdb/applications/applicationgroup?application__name=%s&environment__name=%s' % (self.item, self.env)
            version_path = '/api/cmdb/applications/applicationhistory.json?application_group__application__name=%s&application_group__environment__name=%s&version=%s' % (
                self.item, self.env, self.version)
            self.item_result = api.get(item_path)
            self.version_result = api.get(version_path)

    def __create_mission_control(self):
        mission = Mission.objects.get(mark=str(self.mission_id))
        status = Status.objects.get(content=ReleaseStatus.Undo)
        host_len = len(list(set([x['host'] for x in Progress.objects.filter(mission=mission).values('host')])))
        if self.create_type == 1 or self.create_type == 2:
            Mission_control.objects.create(mission=mission, host=host_len, gray_status=False, status=status, host_done=0)
            if self.create_type == 2 and not self.expand:
                Mission_control.objects.create(mission=mission, host=host_len, gray_status=True, status=status, host_done=0)

    def __create_mission_progress(self, item_list):
        ProgressAct(str(self.mission_id)).create(item_list)

    def __create_mission_before(self, item_type, roll=None):
        if roll:
            self.create_type = 2
            self.mission_type = Type.objects.get(content=ReleaseType.RollBack)
            if self.version_result['count'] == 0:
                raise ReleaseError('this version %s did not publish before' % self.version)
        else:
            if self.env == ReleaseEnv.Staging:
                self.mission_type = Type.objects.get(content=ReleaseType.UpdateStg)
                self.create_type = 1
            else:
                self.create_type = 2
                if item_type in ('iis', 'nodejs', 'java', 'nginx', 'static_win', 'static'):
                    if self.expand:
                        self.mission_type = Type.objects.get(content=ReleaseType.ExpandIIS)
                    else:
                        self.mission_type = Type.objects.get(content=ReleaseType.UpdateIIS)
                elif item_type in ('service', 'handler'):
                    if self.expand:
                        self.mission_type = Type.objects.get(content=ReleaseType.ExpandSrv)
                    else:
                        self.mission_type = Type.objects.get(content=ReleaseType.UpdateSrv)
                else:
                    raise ReleaseError('no this item type %s' % item_type)
                    # close version lock
                    # if self.version_result['count'] != 0:
                    #     raise ReleaseError('mission already existed: %s' % self.version_result['results'][0]['task_id'])

    def __create_mission_after(self):
        self.__create_mission_progress(map(lambda x: dict(location=x['location'], list=x['ipaddresses']), self.item_result['results']))
        self.__create_mission_control()
        return get_result(0, str(self.mission_id))

    @try_except
    def __create_mission(self, roll=None):
        self.__get_item_and_version()
        if self.item_result['count'] != 0:
            dep = self.item_result['results'][0]['department']
            item_type = self.item_result['results'][0]['type'].lower()
            self.__create_mission_before(item_type, roll)
            if roll:
                env = ReleaseEnv.Production
            else:
                env = self.env
            self.mission_id = Mission.objects.create(version=self.version, dep=dep, env=env, item=self.item,
                                                     item_type=item_type, type=self.mission_type, creator=self.creator)
            logger.debug('mission %s created', self.mission_id)
        else:
            raise ReleaseError('application group does not contain this item %s' % self.item)
        return self.__create_mission_after()

    def create(self):
        return self.__create_mission()

    def create_roll(self):
        self.env = ReleaseEnv.Production
        return self.__create_mission(roll=True)

    def create_stg(self):
        self.env = ReleaseEnv.Staging
        return self.__create_mission()

    def create_pro(self):
        self.env = ReleaseEnv.Production
        return self.__create_mission()

    def create_expand(self):
        self.expand = True
        return self.create_pro()


class MissionJobAct(object):
    def __init__(self, mission_id):
        self.mission_id = mission_id

    @try_except
    def complete(self):
        Mission.objects.filter(mark=self.mission_id).update(status=True)
        return get_result(0, 'done!')

    @staticmethod
    def __valid_executing(mission):
        if Mission_control.objects.filter(mission=mission, status__content=ReleaseStatus.Processing).count() > 0:
            raise ReleaseError('some one is executing the mission')

    @try_except
    def reset(self):
        mission = Mission.objects.get(mark=self.mission_id)
        self.__valid_executing(mission)
        undo_status = Status.objects.get(content=ReleaseStatus.Undo)
        Mission_control.objects.filter(mission=mission).update(status=undo_status, order=1, lock_status=False)
        Progress.objects.filter(mission=mission).update(status=undo_status, detail='no result')
        mission.percent = 0
        mission.host_failed = 0
        mission.save()
        return get_result(0, 'done!')

    @try_except
    def cancel(self):
        from ops.celery import app
        while 1:
            reserved_act = app.control.inspect().reserved()
            all_acts = []
            for m in reserved_act['celery@Ops_Dev']:
                n = tuple(eval(m['args']))
                mission, a, b = n
                n_act = {'mission': mission, 'func': m['name'], 'id': m['id']}
                all_acts.append(n_act)
            revoke_list = [x['id'] for x in all_acts if x['mission'] == self.mission_id]
            if len(revoke_list) == 0:
                break
            else:
                for n in revoke_list:
                    app.control.revoke(n)
        return get_result(0, 'done')


class ProgressAct(object):
    def __init__(self, mission_id):
        self.mission_id = mission_id
        self.mission = Mission.objects.get(mark=self.mission_id)

    def valid_exist(self):
        if Progress.objects.filter(mission=self.mission_id).count() > 0:
            raise ReleaseError('already existed!')

    @try_except
    def create(self, item_list):
        self.valid_exist()
        status = Status.objects.get(content=ReleaseStatus.Undo)
        step_detail = Type_step.objects.filter(type=self.mission.type)
        for m in step_detail:
            step = m.step
            for n in item_list:
                for i in n['list']:
                    Progress.objects.create(host=i, step=step, dep=self.mission.dep, item=self.mission.item, item_type=self.mission.item_type,
                                            type=self.mission.type, env=self.mission.env, step_order=m.order,
                                            mission=self.mission, location=n['location'], status=status)
        return get_result(0, 'done!')

    @staticmethod
    def __get_list(item, env):
        item_path = '/api/cmdb/applications/applicationgroup?application__name=%s&environment__name=%s' % (item, env)
        return [dict(location=m['location'], list=m['ipaddresses']) for m in CmdbApi().get(item_path)['results']]

    def __valid_executing(self):
        if ReleaseStatus.Processing in [x.status.content for x in Mission_control.objects.filter(mission=self.mission)]:
            raise ReleaseError('some one is executing the mission!')

    @try_except
    def rebuild(self):
        self.__valid_executing()
        env = self.mission.env
        status = Status.objects.get(content=ReleaseStatus.Undo)
        cmdb_list = self.__get_list(self.mission.item, env)
        logger.debug('cmdb_list: %s' % cmdb_list)
        # fixme: host location change cause rebuild bug
        for idc in cmdb_list:
            existed_list = list(set([x.host for x in Progress.objects.filter(mission=self.mission, location=idc['location']).all()]))
            for ip in [x for x in existed_list if x not in idc['list']]:
                Progress.objects.filter(host=ip, mission=self.mission).delete()
            step_list = Type_step.objects.filter(type=self.mission.type)
            for step in step_list:
                for ip in [x for x in idc['list'] if x not in existed_list]:
                    Progress.objects.filter(~Q(location=idc['location']), host=ip, mission=self.mission).delete()
                    Progress.objects.create(host=ip, step=step.step, dep=self.mission.dep, item=self.mission.item, item_type=self.mission.item_type, type=self.mission.type,
                                            env=env, location=idc['location'], step_order=step.order, mission=self.mission, status=status)
        return get_result(0, 'done!')

    @try_except
    def get(self):
        result = dict(mission=self.mission_id, control=MissionControlAct(self.mission_id).get())
        progress_list = []
        # for m in Progress.objects.filter(mission=self.mission).values('host').distinct():
        for m in list(set([x.host for x in Progress.objects.filter(mission=self.mission)])):
            t_result = dict(name=m, location=Progress.objects.filter(mission=self.mission, host=m)[0].location)
            p_result = []
            for n in Progress.objects.filter(host=m, mission=self.mission):
                if n.step.content == ReleaseStep.Complete:
                    t_result['status'] = STATUS_LIST[n.status.content]
                p_result.append(dict(step=n.step.alias, order=n.step_order, status=STATUS_LIST[n.status.content], detail=n.detail,time=(n.modified_date+datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')))
            t_result.update(progress=p_result)
            progress_list.append(t_result)
        result.update(host=progress_list)
        return result


class MissionControlAct(object):
    def __init__(self, mission_id):
        self.mission_id = mission_id

    def get(self):
        return [self.__format_control(p) for p in Mission_control.objects.filter(mission__mark=self.mission_id)]

    @staticmethod
    def __format_control(p):
        control = dict(status=STATUS_LIST[p.status.content], id=p.id)
        if p.gray_status:
            control.update(name=ExecName.gray)
        else:
            control.update(name=ExecName.one)
        return control


class PackageAdmin(object):
    git_map = {
        'control.ops.ymatou.cn': 'cmd_controller',
        'release.ops.ymatou.cn': 'release',
        'saltapi.ops.ymatou.cn': 'salt-api',
        'lbadmin.ops.ymatou.cn': 'lbadmin'
    }

    def __init__(self, app, version):
        self.app = app
        self.version = version
        if 'ymatou.cn' not in app:
            self.app = '%s.ops.ymatou.cn' % self.app
        self.git_path = self.git_map.get(self.app)

    @staticmethod
    def shell(cmd):
        rs = commands.getoutput(cmd)
        print 'cmd %s' % cmd

    @try_except
    def run(self):
        if self.app:
            self.shell('rm -rf  /tmp/git/%s' % self.app)
            self.shell('git clone git@gitlab.ops.ymt.corp:devops/%s.git  /tmp/git/%s' % (self.git_path, self.app))
            self.shell('cd /tmp/git/%s && echo %s>YMTVersion.txt' % (self.app, self.version))
            self.shell('cd /tmp/git/%s && zip -r %s.zip ./*' % (self.app, self.app))
            self.shell('cd /tmp/git/%s && md5sum %s.zip >%s.md5' % (self.app, self.app, self.app))
            self.upload_ftp(self.app, self.version)
            return get_result(0, 'package %s %s ok' % (self.app, self.version))
        else:
            raise NameError('no app')

    @staticmethod
    def upload_ftp(app, version):
        ftp = FTP('222.73.158.121')
        ftp.login('wdeployadmin', 'wdeployadmin')
        zip_file = '/tmp/git/%s/%s.zip' % (app, app)
        md5_file = '/tmp/git/%s/%s.md5' % (app, app)
        try:
            ftp.mkd('production/devops/%s' % app)
        except Exception, e:
            print str(e)
        try:
            ftp.mkd('production/devops/%s/%s' % (app, version))
        except Exception, e:
            print str(e)

        ftp.storbinary('STOR production/devops/%s/%s/%s.zip' % (app, version, version), open(zip_file, 'rb'))
        ftp.storbinary('STOR production/devops/%s/%s/%s.md5' % (app, version, version), open(md5_file, 'rb'))
