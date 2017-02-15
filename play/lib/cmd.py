# coding=utf-8
from core.common import ReleaseStep, ReleaseStatus, RETCODE, STDOUT, STDERR, ReleaseApiStep, get_result, ReleaseError
from play.lib import BaseTask, get_status
from release.models import Mission, Log_progress, Status, Progress
from release_action.api import CmdbApi
from release_action.cmd import CmdGetPackage, CmdGetConfiguration, CmdGetProduction, CmdUpdate, CmdUploadProduction, CmdRollBack, CmdVersionCheck, CmdComplete, CmdLB, CmdHbCheck, CmdWarm


class CmdRunTask(BaseTask):
    salt_cmd_map = {
        ReleaseStep.GetPackage: CmdGetPackage,
        ReleaseStep.GetConfiguration: CmdGetConfiguration,
        ReleaseStep.GetProduction: CmdGetProduction,
        ReleaseStep.Update: CmdUpdate,
        ReleaseStep.UploadProduction: CmdUploadProduction,
        ReleaseStep.RollBack: CmdRollBack,
        ReleaseStep.VersionCheck: CmdVersionCheck,
        ReleaseStep.Complete: CmdComplete
    }
    mission_id, host = None, None
    order, exec_id, mission = None, None, None

    def init(self, mission_id, host, order, exec_id=0):
        self.mission_id = mission_id
        self.host = host
        self.order = order
        self.exec_id = exec_id
        self.mission = Mission.objects.get(mark=self.mission_id)
        super(CmdRunTask, self).init()

    def __log_progress_create(self, status, step, result, detail=''):
        Log_progress.objects.create(status=status, type=self.mission.type, step=step, host=self.host, dep=self.mission.dep,
                                    item=self.mission.item, step_order=self.order, mission=self.mission, result=result, detail=detail)

    def __start(self):
        start_status = Status.objects.get(content=ReleaseStatus.Processing)
        self.progress = Progress.objects.get(mission=self.mission, host=self.host, step_order=self.order)
        self.progress.status = start_status
        self.progress.save()
        self.__log_progress_create(status=start_status, step=self.progress.step, result='start')

    def __save_progress_status(self, result):
        # default status
        end_status = get_status(ReleaseStatus.Failed)
        if RETCODE in result.keys():
            if result[RETCODE] == 0:
                end_status = get_status(ReleaseStatus.Done)
                self.progress.detail = str(result[STDOUT])
                self.__log_progress_create(status=end_status, step=self.progress.step, detail=str(result[STDOUT]), result='stop')
            elif result[RETCODE] == 1:
                if self.progress.step.content == ReleaseStep.Complete:
                    end_status = Status.objects.get(content=ReleaseStatus.Undo)
                    self.progress.detail = 'failed'
                else:
                    self.progress.detail = str(result[STDERR])
                self.__log_progress_create(status=end_status, step=self.progress.step, detail=str(result[STDERR]), result='end')
            else:
                self.progress.detail = 'unknown retcode %s' % result[RETCODE]
        else:
            self.progress.detail = 'result did not contain retcode %s' % str(result)
        self.progress.status = end_status
        self.progress.save()

    def run(self, mission_id, host, order, exec_id=0):
        self.init(mission_id, host, order, exec_id=exec_id)
        self.__start()
        result = None
        try:
            if self.progress.step.content in self.salt_cmd_map:
                cls_cmd = self.salt_cmd_map.get(self.progress.step.content)
                result = cls_cmd(self.host, self.progress.location, self.mission.item_type, self.mission.dep, self.mission.item, self.mission.version).run()
            elif self.progress.step.content == ReleaseApiStep.LBUp \
                    or self.progress.step.content == ReleaseApiStep.LBDown \
                    or self.progress.step.content == ReleaseApiStep.LBAdd:
                cmd_query = CmdbApi()
                if self.progress.step.content == ReleaseApiStep.LBUp:
                    result = CmdLB(self.host, self.progress.location, self.mission.item, cmd_query).lb_up()
                elif self.progress.step.content == ReleaseApiStep.LBDown:
                    result = CmdLB(self.host, self.progress.location, self.mission.item, cmd_query).lb_down()
                elif self.progress.step.content == ReleaseApiStep.LBAdd:
                    result = CmdLB(self.host, self.progress.location, self.mission.item, cmd_query).lb_add()
            elif self.progress.step.content == ReleaseApiStep.HBCheck:
                result = CmdHbCheck(self.host, self.mission.item).run()
            elif self.progress.step.content == ReleaseApiStep.Warm:
                cmd_query = CmdbApi()
                result = CmdWarm(self.host, self.mission.item, cmd_query).run()
                # if self.mission.item_type == "iis" :
                #     cmd_query = CmdbApi()
                #     # 1分钟 重试 3次
                #     result = CmdWarm(self.host, self.mission.item, cmd_query).run()
                # else:
                #     result = get_result(0, '非IIS不做检查')
            else:
                raise ReleaseError('%s this act to do ' % self.progress.step.content)
        except Exception, e:
            result = get_result(1, str(e))
        finally:
            self.__save_progress_status(result)
            return result
