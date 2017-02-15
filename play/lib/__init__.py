# coding=utf-8

from celery import Task

from core.common import logger, ReleaseStep, ReleaseStatus
from release.models import Progress, Step, Mission_control, Status


def get_status(status):
    return Status.objects.get(content=status)


def get_step(step):
    return Step.objects.get(content=step)


def get_todo(exec_id):
    return Mission_control.objects.get(id=exec_id)


class BaseTask(Task):
    abstract = True
    logger = logger

    def init(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        pass

    def static_mission_stats(self, gray_status):
        self.static_mission_percent(gray_status)
        self.static_mission_error_host()

    def static_mission_error_host(self):
        kwargs = dict(mission=self.mission, step=get_step(ReleaseStep.Complete))
        self.mission.host_failed = Progress.objects.filter(status__content=ReleaseStatus.Failed, **kwargs).all().count()
        self.mission.save()

    def static_mission_percent(self, gray_status):
        kwargs = dict()
        if not gray_status:
            kwargs = dict(step__in=Step.objects.filter(gray_status=False).all())
        all_progress = Progress.objects.filter(mission=self.mission, **kwargs).count()
        undo_progress = Progress.objects.filter(mission=self.mission, status=get_status(ReleaseStatus.Undo), **kwargs).count()
        self.logger.debug('%s' % self.mission)
        if all_progress:
            self.mission.percent = int(float(all_progress - undo_progress) / float(all_progress) * 100)
        self.logger.debug('all_progress:%s undo_progress:%s done_percent:%s' % (all_progress, undo_progress, self.mission.percent))
        self.mission.save()


