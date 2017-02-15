# coding=utf-8
from celery import chain
from core.common import logger, ReleaseStatus, get_result
from ops.settings import GRAY_COUNT_DOWN, DEFAULT_COUNT_DOWN
from release.models import Mission_control
from play.lib.base import PublishBaseTask
from play.lib.cmd import CmdRunTask
from play.lib.version import VersionConfirmTask
from play.lib.host import ProgressHostRunTask


class TemplatePublishTask(PublishBaseTask):
    """
    发布模板
    """
    gray_status = False
    abstract = True

    def get_finish_status(self, complete_count, host_list):
        return complete_count == len(host_list)

    def core(self, host_list):
        if self.todo.order == 1:
            return self.progress_host_task(host_list, order=2, countdown=DEFAULT_COUNT_DOWN)
        elif self.todo.order == 2:
            return self.check_complete(host_list, countdown=DEFAULT_COUNT_DOWN)

    def rerun(self, countdown=None):
        raise NotImplementedError


class RapidPublishTask(TemplatePublishTask):
    """
    快速发布
    多台分片进行发布 单台发布失败不影响其他发布
    """

    def rerun(self, countdown=None):
        try:
            result = RapidPublishTask().apply_async(args=(self.exec_id,), countdown=countdown)
            logger.info("publish RapidPublishTask<{0}>: {1}".format(result.task_id, self.mission))
        except Exception as e:
            logger.error("publish RapidPublishTask {0} fail: {1}".format(self.mission, e))


class RollPublishTask(TemplatePublishTask):
    """
    滚动发布
    逐台发布 一台失败即任务失败
    """

    def progress_host_task(self, todo_host, order, countdown=None):
        host_list = []
        for i in range(0, len(todo_host)):
            if todo_host[i]:
                if i == 0:
                    host_list.append(ProgressHostRunTask().s(get_result(0, ''), self.mission, todo_host[i], self.gray_status, exec_id=self.exec_id))
                else:
                    host_list.append(ProgressHostRunTask().s(self.mission, todo_host[i], self.gray_status, exec_id=self.exec_id))
        chain(host_list).delay()
        self.update_todo(order=order)
        self.rerun(countdown=countdown)
        return 'add to the celery'

    def rerun(self, countdown=None):
        try:
            result = RollPublishTask().apply_async(args=(self.exec_id,), countdown=countdown)
            logger.info("publish RollPublishTask<{0}>: {1}".format(result.task_id, self.mission))
        except Exception, e:
            logger.error("publish RollPublishTask {0} fail: {1}".format(self.mission, e))


class GrayPublishTask(PublishBaseTask):
    gray_status = True

    @staticmethod
    def get_gray_finish_status(all_host, order):
        for m in all_host.keys():
            done_hosts = len([x for x in all_host[m] if x['status'] == ReleaseStatus.Done])
            if (order == 2 and done_hosts != 1) or (order == 3 and done_hosts * 10 / len(all_host[m])) \
                    or (order == 4 and done_hosts * 10 / len(all_host[m]) <= 9):
                return False
        return True

    def get_finish_status(self, complete_count, host_list):
        return self.get_gray_finish_status(self.get_processing_host(), 4)

    def rerun(self, countdown=None):
        try:
            result = GrayPublishTask().apply_async(args=(self.exec_id,), countdown=countdown)
            logger.info("publish GrayPublishTask<{0}>: {1}".format(result.task_id, self.mission))
        except Exception, e:
            logger.error("publish GrayPublishTask {0} fail: {1}".format(self.mission, e))

    def check_finish_status(self, order, countdown=DEFAULT_COUNT_DOWN, redo=True):
        all_host = self.get_processing_host()
        self.valid_failed_host(all_host)
        if self.get_gray_finish_status(all_host, order):
            todo_host = []
            for m in all_host.keys():
                if order == 1:
                    todo_host = [all_host[x][0]['host'] for x in all_host.keys()]
                elif order == 2:
                    undo_host = [x['host'] for x in all_host[m] if x['status'] == ReleaseStatus.Undo]
                    todo_host.extend(undo_host[:len(undo_host) / 2])
                elif order == 3:
                    todo_host.extend([x['host'] for x in all_host[m] if x['status'] == ReleaseStatus.Undo])
            self.progress_host_task(todo_host, order=order + 1, countdown=GRAY_COUNT_DOWN)
        else:
            if redo:
                self.rerun(countdown=countdown)

    def core(self, host_list):
        self.logger.debug('start gray:%s' % self.todo.gray_status)
        if self.todo.order == 1:
            self.check_finish_status(order=1, redo=False)
        elif self.todo.order == 2:
            self.check_finish_status(order=2, countdown=60)
        elif self.todo.order == 3:
            self.check_finish_status(order=3)
        elif self.todo.order == 4:
            self.check_complete(host_list, countdown=DEFAULT_COUNT_DOWN)
        return 'all done'


class PublishTask(object):
    def __init__(self, exec_id, roll=None):
        self.exec_id = exec_id
        self.todo_mission_control = Mission_control.objects.get(id=exec_id)
        self.mission = self.todo_mission_control.mission
        self.roll = roll

    def run(self):
        if self.todo_mission_control.gray_status:
            return GrayPublishTask().run(self.exec_id)
        else:
            if self.roll:
                return RollPublishTask().run(self.exec_id)
            else:
                return RapidPublishTask().run(self.exec_id)
