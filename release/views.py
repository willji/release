from rest_framework import permissions
# Create your views here.
from rest_framework import viewsets
from rest_framework import filters
from django.db.models import Q
from serializers import TypeSerializer, StepSerializer, Type_stepSerializer, \
    MissionSerializer, ProgressSerializer, \
    LogProgressSerializer, StatusSerializer, MissionControlSerializer
from models import Type, Step, Mission, Progress, Log_progress, Status, Type_step, Mission_control


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.DjangoModelPermissions,)
    filter_backends = (filters.DjangoFilterBackend,)

    def perform_create(self, serializer):
        return super(BaseViewSet, self).perform_create(serializer)


class StatusViewSet(BaseViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    filter_fields = ('content',)


class TypeViewSet(BaseViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    filter_fields = ('content',)


class StepViewSet(BaseViewSet):
    queryset = Step.objects.all()
    serializer_class = StepSerializer
    filter_fields = ('content',)


class TypeStepViewSet(BaseViewSet):
    queryset = Type_step.objects.all()
    serializer_class = Type_stepSerializer
    filter_fields = ('type', 'step',)


class MissionViewSet(BaseViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('^item', '^creator', '^version')
    filter_fields = ('status', 'timeout_status', 'creator', 'item', 'version')


class ReleaseMissionSet(MissionViewSet):
    """
    release mission
    """
    queryset = Mission.objects.filter(~Q(type__content__contains='expand'))


class ExpandMissionSet(MissionViewSet):
    """
    expand mission
    """
    queryset = Mission.objects.filter(type__content__contains='expand')


class ProgressViewSet(BaseViewSet):
    queryset = Progress.objects.all()
    serializer_class = ProgressSerializer
    filter_fields = ('mission', 'status', 'host')


class LogProgressViewSet(BaseViewSet):
    queryset = Log_progress.objects.all()
    serializer_class = LogProgressSerializer
    filter_fields = ('mission', 'host',)


class MissionControlViewSet(BaseViewSet):
    queryset = Mission_control.objects.all()
    serializer_class = MissionControlSerializer
    filter_fields = ('mission',)
