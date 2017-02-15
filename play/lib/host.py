# coding=utf-8
from core.common import ReleaseStatus, ReleaseError, get_result, ReleaseStep
from play.lib import BaseTask, get_step, get_status
from play.lib.cmd import CmdRunTask
from release.models import Progress


class ProgressHostRunTask(BaseTask):
    mission = None

    def init(self, rs, mission):
        self.mission = mission
        self.rs = rs
        super(ProgressHostRunTask, self).init()
        if self.rs["retcode"] == 1:
            raise ReleaseError('滚动发布失败')

    @staticmethod
    def __phrase_gary_status(gray_status):
        if isinstance(gray_status, unicode):
            return eval(gray_status)
        else:
            return gray_status

    def run(self, rs, mission, host, gray_status, exec_id=0):
        try:
            self.init(rs, mission)
            self.logger.debug('%s %s' % (self.mission, host))
            for id_order in range(1, Progress.objects.filter(mission=self.mission, host=host).count() + 1):
                progress = Progress.objects.get(mission=self.mission, host=host, step_order=id_order)
                if self.__phrase_gary_status(gray_status) or not progress.step.gray_status:
                    cmd_result = CmdRunTask().run(self.mission.mark, host, id_order, exec_id=exec_id)
                    self.static_mission_stats(self.__phrase_gary_status(gray_status))
                    progress = Progress.objects.get(mission=self.mission, host=host, step_order=id_order)
                    if progress.status.content != ReleaseStatus.Done:
                        raise ReleaseError('run %s on %s failed.result is:%s' % (progress.step.alias, host, str(cmd_result)))
            return get_result(0, 'all done!')
        except Exception, e:
            Progress.objects.filter(mission=self.mission, host=host, step=get_step(ReleaseStep.Complete)).update(status=get_status(ReleaseStatus.Failed), detail=str(e))
            self.static_mission_stats(self.__phrase_gary_status(gray_status))
            return get_result(1, str(e))
