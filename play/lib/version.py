# coding=utf-8
from core.common import try_except, get_result
from play.lib import BaseTask
from release_action.api import CmdbApi


class VersionConfirmTask(BaseTask):
    mission = None

    def init(self, mission):
        self.mission = mission
        super(VersionConfirmTask, self).init()

    @try_except
    def run(self, mission):
        self.init(mission)
        api = CmdbApi()
        version_add_url = '/api/cmdb/applications/applicationhistory'
        item_check_url = '/api/cmdb/applications/applicationgroup?application__name=%s&environment__name=%s' % (self.mission.item, self.mission.env)
        for m in api.get(item_check_url)['results']:
            to_add_url = '/' + '/'.join(m['url'].split('/')[-5:])
            api.update(to_add_url, {'version': self.mission.version})
            api.create(version_add_url, dict(application_group=m['display_name'], version=self.mission.version, task_id=str(self.mission.mark)))
        return get_result(0, 'done')
