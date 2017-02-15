from django.test import TestCase
from django.test.utils import override_settings
from release import act
from release_action.tasks import PublishTask
from release.models import Mission_control, Mission, Log_progress, Step, Progress
from release_action.act import ProgressActAdmin
from release_action.cmd import CmdLB
from release_action.api import CmdbApi


class MissionTestCase(TestCase):
    fixtures = ['ops/init.json']

    def setUp(self):
        super(MissionTestCase, self).setUp()
        self.item = 'haiwai.ymatou.com'
        self.version = 'T0003'
        self.creator = 'anonymous'
        self.env = 'T1'
        item_data = {'count': 1, 'results': [{'department': 'm2c', 'type': 'iis', 'location': 'T3', 'ipaddresses': ['172.16.7.3']}]}
        version_data = {'count': 0, 'results': {}}
        self.mock_data = item_data, version_data

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True, BROKER_BACKEND='memory',
                       CELERY_ALWAYS_EAGER=True)
    def test_release(self):
        self.mission_create()
        # for mission in Mission.objects.all():
        #     print '#'*5, mission.type_id
        # self.progress_one()
        self.task_start()
        print Progress.objects.all().values('host')


        # self.show_log()
        # for mission in Mission.objects.all():
        #     print mission.percent

    def mission_create(self):
        result = act.MissionAct(item=self.item, env=self.env, version=self.version, creator=self.creator, mock_data=self.mock_data).create_pro()
        print result
        self.assertEquals(result['retcode'], 0)

    def task_start(self):
        for mission_control in Mission_control.objects.all():
            print PublishTask(exec_id=mission_control.id).run()

    def progress_one(self):
        for mission in Mission.objects.all():
            print ProgressActAdmin().progress_one(mission.mark, '172.16.100.80', 1)

    def show_log(self):
        for log in Log_progress.objects.all():
            print '#' * 5, log.detail, log.result

    def test_cmd(self):
        CmdLB('172.16.100.80', 'T1', 'haiwai.ymatou.com', CmdbApi()).run('lb-add')

    def tearDown(self):
        pass
