# coding=utf-8
from core.common import try_except, ReleaseEnv, get_result, ReleaseError
from play.lib import BaseTask
from release_action.api import JiraApi


class JiraCallbackTask(BaseTask):
    mission = None

    def init(self, mission):
        self.mission = mission
        super(JiraCallbackTask, self).init()

    @try_except
    def run(self, mission):
        self.init(mission)
        api = JiraApi()
        query_path = '/api/issues?task_id=%s' % self.mission.mark
        query_result = api.get(query_path)
        if self.mission.env == ReleaseEnv.Staging:
            status = dict(status=u"STAGE发布成功")
        else:
            status = dict(status=u"生产发布成功")
        if query_result['count'] == 1:
            jira_path = query_result['results'][0]['url']
            t_result = api.update(jira_path, status)
            if t_result == 200:
                return get_result(0, 'done')
            else:
                raise ReleaseError('fail to patch %s' % jira_path)
        else:
            raise ReleaseError('jira does not contain this mission %s' % self.mission.mark)

