from django.db.models import Q

from core.common import ReleaseStep, ReleaseStatus, ReleaseError, get_result
from ops.settings import GRAY_PUBLISH_NUMBER, DEFAULT_COUNT_DOWN
from play.lib import BaseTask, get_todo, get_step, get_status
from play.lib.version import VersionConfirmTask
from play.lib.host import ProgressHostRunTask
from release.models import Progress, Mission_control


class PublishBaseTask(BaseTask):
    abstract = True
    exec_id, todo, gray_status = None, None, None
    mission = None

    def init(self, exec_id):
        self.exec_id = exec_id
        self.todo = get_todo(exec_id)
        self.mission = self.todo.mission
        self.gray_status = self.todo.gray_status
        self.static_mission_stats(self.gray_status)

    def get_processing_host(self):
        all_host_detail = Progress.objects.filter(mission=self.mission, step=get_step(ReleaseStep.Complete)).values('host', 'location', 'id')
        all_host = {}
        for location in list(set(x['location'] for x in all_host_detail)):
            all_host[location] = [{'host': x['host'], 'status': Progress.objects.get(id=x['id']).status.content} for x in all_host_detail if x['location'] == location]
        return all_host

    def valid_is_executing(self):
        if self.todo.status.content == ReleaseStatus.Undo:
            if Mission_control.objects.filter(Q(mission=self.mission), Q(status__content=ReleaseStatus.Processing) | Q(status__content=ReleaseStatus.Suspend)).count() > 0:
                raise ReleaseError('someone is executing the mission')

    def core(self, host_list):
        pass

    def update_todo(self, order=None, status=None, lock_status=None):
        if order:
            self.todo.order = order
        if status:
            self.todo.status = get_status(status)
        if isinstance(lock_status, bool):
            self.todo.lock_status = lock_status
        self.todo.save()

    def valid_failed_host(self, all_host):
        for m in all_host.keys():
            if len([x for x in all_host[m] if x['status'] == ReleaseStatus.Failed]) > 0:
                self.update_todo(status=ReleaseStatus.Suspend, lock_status=False)
                raise ReleaseError('some host exec failed')

    def check_complete(self, host_list, countdown=None):
        kwargs = dict(mission=self.mission, host__in=host_list, step=get_step(ReleaseStep.Complete))
        complete_count = Progress.objects.filter(status__content=ReleaseStatus.Done, **kwargs).count()
        finish_count = Progress.objects.filter(Q(status__content=ReleaseStatus.Failed) | Q(status__content=ReleaseStatus.Done), **kwargs).count()
        return self.check_host_done(host_list, complete_count, finish_count, countdown)

    def check_host_done(self, host_list, complete_count, finish_count, countdown):
        if finish_count == len(host_list):
            self.__unlock_mission()
            if self.get_finish_status(complete_count, host_list):
                self.update_todo(status=ReleaseStatus.Done)
                VersionConfirmTask().run(self.mission)
                # JiraCallbackTask().run(self.mission)
                result = 'all done'
            else:
                self.update_todo(status=ReleaseStatus.Failed)
                result = 'has some hosts exec failed'
        else:
            result = 'not complete'
            self.rerun(countdown=countdown)
        return result

    def get_finish_status(self, complete_count, host_list):
        pass

    def __unlock_mission(self):
        self.update_todo(lock_status=False)

    def progress_host_task(self, todo_host, order, countdown=None):
        for i in range(0, len(todo_host)):
            if todo_host[i]:
                countdown = (i % 5) * 30
                if self.mission.type.content.__contains__("expand"):
                    countdown = i * 60
                ProgressHostRunTask().apply_async(args=(get_result(0, ''), self.mission, todo_host[i], self.gray_status), kwargs=dict(exec_id=self.exec_id), countdown=countdown)
        self.update_todo(order=order)
        self.rerun(countdown=countdown)
        return 'add to the celery'

    def rerun(self, countdown=None):
        pass

    def valid_run(self):
        # if self.todo.lock_status:
        #     raise ReleaseError('this mission is executing')
        if self.todo.gray_status:
            if len(list(set([x['host'] for x in Progress.objects.filter(mission=self.mission).values('host')]))) < GRAY_PUBLISH_NUMBER:
                raise ReleaseError('not enough host to exec the gray publish')

    def run(self, exec_id):
        self.init(exec_id=exec_id)
        try:
            self.valid_run()
            self.valid_is_executing()
            if self.todo.status.content in [ReleaseStatus.Undo, ReleaseStatus.Processing]:
                if self.todo.status.content == ReleaseStatus.Undo:
                    self.__lock_mission()
                self.update_todo(status=ReleaseStatus.Processing)
                result = self.core(list(set([x['host'] for x in Progress.objects.filter(mission=self.mission).values('host')])))
            elif self.todo.status.content == ReleaseStatus.Suspend:
                self.rerun(countdown=DEFAULT_COUNT_DOWN)
                result = 'mission suspended'
            else:
                self.__unlock_mission()
                if self.todo.status.content == ReleaseStatus.Done:
                    result = 'all done'
                elif self.todo.status.content == ReleaseStatus.Failed:
                    result = 'exec failed'
                else:
                    raise ReleaseError('unknown status %s' % self.todo.status.content)
            return get_result(0, result)
        except Exception, e:
            self.__unlock_mission()
            return get_result(1, str(e))

    def __lock_mission(self):
        self.update_todo(lock_status=True)
