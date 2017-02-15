from unittest import TestCase
from release_action.api import ReleaseApi, CmdApi


class MissionTestCase(TestCase):
    def setUp(self):
        self.host = 'release.dev.ymatou.cn'
        self.mission_id = '33055f7aa2184b9c86ab2027d91833fb'
        self.kwargs = dict(host=self.host, user='admin', passwd='admin')
        pass

    def tearDown(self):
        pass

    def test_api(self):
        self.mission_create_expand()
        # self.mission_create_stg()
        # self.progress_get()
        # self.progress_one()
        # self.mission_redo()
        # self.control_do()

    def control_do(self):
        self.send_data = {
            'host': '172.16.100.80',
            'module_name': 'get_package',
            'arg': (u'iis', u'production/m2c/haiwai.ymatou.com/T2', u'172.16.100.81,wdeployadmin,wdeployadmin')
        }
        print CmdApi('cmd_control').post(self.send_data)

    def progress_get(self):
        data = {'mission': self.mission_id}
        ReleaseApi(cmd_path='http://%s/progress/get' % self.host, **self.kwargs).post(data)

    def mission_create_stg(self):
        data = {'item': 'haiwai.ymatou.com', 'version': 'T67807'}
        print ReleaseApi(cmd_path='http://%s/mission/create/stg' % self.host, **self.kwargs).post(data)

    def mission_create_expand(self):
        data = {'creator': 'huamaolin', 'item': 'haiwai.ymatou.com', 'version': 'T00003',
                'data': {'count': 3, 'results': [{'department': 'm2c', 'type': 'iis', 'location': 'T1', 'ipaddresses': ['172.16.100.80']}]}}
        print ReleaseApi(cmd_path='http://%s/mission/create/expand' % self.host, **self.kwargs).post(data)

    def progress_one(self):
        data = {'mission': self.mission_id, 'host': '172.16.100.80', 'order': 1}
        ReleaseApi(cmd_path='http://%s/progress/one' % self.host).post(data)

    def mission_redo(self):
        data = {'mission': self.mission_id}
        ReleaseApi(cmd_path='http://%s/mission/redo' % self.host, host=self.host).post(data)
