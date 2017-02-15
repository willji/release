from release.models import Mission, Mission_control, Progress, Log_progress, Status, Step, Type_step
from django.contrib import admin


class MinionAdmin(admin.ModelAdmin):
    list_display = ('mark', 'version', 'dep', 'env', 'item', 'item_type', 'type', 'percent', 'host_failed', 'status', 'timeout_status', 'creator', 'created_date')
    list_filter = ('version', 'dep', 'env', 'item', 'item_type', 'type', 'status', 'creator')
    fields = ('version', 'dep', 'env', 'item', 'item_type', 'type', 'status', 'host_failed', 'timeout_status', 'creator')
    search_fields = ('mark', 'version')


class Mission_controlAdmin(admin.ModelAdmin):
    list_display = ('mission', 'host', 'host_done', 'order', 'times', 'gray_status', 'status', 'lock_status', 'created_date')
    list_filter = ('host', 'host_done', 'order', 'times', 'gray_status', 'status', 'lock_status')
    fields = ('host', 'host_done', 'order', 'times', 'gray_status', 'status', 'lock_status')
    search_fields = ('mission', 'host')


class ProgressAdmin(admin.ModelAdmin):
    list_display = ('host', 'status', 'mission', 'type', 'step', 'dep', 'item', 'location', 'item_type', 'env', 'step_order', 'detail', 'created_date')
    list_filter = ('host', 'status', 'type', 'step', 'dep', 'item', 'location', 'item_type', 'env', 'step_order')
    fields = ('host', 'status', 'mission', 'type', 'step', 'dep', 'item', 'location', 'item_type', 'env', 'step_order', 'detail')
    search_fields = ('host', 'detail')


class Log_progressAdmin(admin.ModelAdmin):
    list_display = ('host', 'status', 'mission', 'type', 'step', 'dep', 'item', 'step_order', 'detail', 'result', 'created_date')
    list_filter = ('host', 'status', 'mission', 'type', 'step', 'dep', 'item', 'step_order')
    fields = ('host', 'status', 'mission', 'type', 'step', 'dep', 'item', 'step_order', 'detail')
    search_fields = ('host', 'mission')


class StatusAdmin(admin.ModelAdmin):
    list_display = ('content', 'alias')
    list_filter = ('content', 'alias')
    fields = ('content', 'alias')
    search_fields = ('content', 'alias')


class StepAdmin(admin.ModelAdmin):
    list_display = ('content', 'alias', 'gray_status')
    list_filter = ('content', 'alias', 'gray_status')
    fields = ('content', 'alias', 'gray_status')
    search_fields = ('content', 'alias')


class Type_stepAdmin(admin.ModelAdmin):
    list_display = ('type', 'step', 'order')
    list_filter = ('type', 'step', 'order')
    fields = ('type', 'step', 'order')
    search_fields = ('type', 'step')


admin.site.register(Type_step, Type_stepAdmin)
admin.site.register(Step, StepAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Log_progress, Log_progressAdmin)
admin.site.register(Progress, ProgressAdmin)
admin.site.register(Mission_control, Mission_controlAdmin)
admin.site.register(Mission, MinionAdmin)
