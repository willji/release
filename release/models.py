# coding=utf-8
from django.db import models
import uuid


class Status(models.Model):
    """
    status model include content and alias
    """
    content = models.CharField(max_length=100, unique=True)
    alias = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.alias


class Step(models.Model):
    """
    step model include content ,alias and gray-status
    """
    content = models.CharField(max_length=100, unique=True)
    alias = models.CharField(max_length=100, unique=True)
    gray_status = models.BooleanField(default=1)

    def __unicode__(self):
        return self.alias


class Type(models.Model):
    """
    type model include content and alias
    """
    content = models.CharField(max_length=100, unique=True)
    alias = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.alias


class Type_step(models.Model):
    """
    relationship between the type and step include type step and order ,type and step are ForeignKeys
    """
    type = models.ForeignKey(Type)
    step = models.ForeignKey(Step)
    order = models.IntegerField(db_index=True)

    def __unicode__(self):
        return self.step.alias


class Mission(models.Model):
    """
    mission model
    """
    mark = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    version = models.CharField(max_length=300)
    dep = models.CharField(max_length=300)
    env = models.CharField(max_length=300)
    item = models.CharField(max_length=300)
    item_type = models.CharField(max_length=300, default='iis')
    type = models.ForeignKey(Type)
    status = models.BooleanField(default=0)
    timeout_status = models.BooleanField(default=0)
    percent = models.IntegerField(default=0)
    host_failed = models.IntegerField(default=0)
    creator = models.CharField(max_length=100, default='ops', db_index=True)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __unicode__(self):
        return str(self.mark)


class Progress(models.Model):
    """
    progress model
    """
    host = models.CharField(max_length=100, db_index=True)
    status = models.ForeignKey(Status, related_name='progress_status')
    mission = models.ForeignKey(Mission)
    type = models.ForeignKey(Type)
    step = models.ForeignKey(Step)
    dep = models.CharField(max_length=300)
    item = models.CharField(max_length=300)
    location = models.CharField(max_length=300, default='T1')
    item_type = models.CharField(max_length=300, default='iis')
    env = models.CharField(max_length=300)
    step_order = models.IntegerField()
    detail = models.TextField(default='no result')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['mission', 'step_order']

    def __unicode__(self):
        return self.host


class Log_progress(models.Model):
    host = models.CharField(max_length=100)
    status = models.ForeignKey(Status, related_name='log_status')
    mission = models.ForeignKey(Mission)
    step = models.ForeignKey(Step)
    type = models.ForeignKey(Type)
    dep = models.CharField(max_length=300)
    item = models.CharField(max_length=300)
    step_order = models.IntegerField()
    detail = models.TextField(default='none')
    result = models.CharField(max_length=100, default='none')
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.host

    class Meta:
        ordering = ['-created_date']


class Mission_control(models.Model):
    mission = models.ForeignKey(Mission)
    host = models.IntegerField()
    host_done = models.IntegerField()
    order = models.IntegerField(default=1)
    times = models.IntegerField(default=1)
    gray_status = models.BooleanField(db_index=True)
    status = models.ForeignKey(Status, related_name='control_status')
    lock_status = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return str(self.mission)
