# code=utf-8
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
import ast
from release_action.act import ProgressActAdmin, workflow_get, workflow_update, mission_exec_status
from release.act import MissionAct, MissionJobAct, ProgressAct
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from release.models import Mission
from play.tasks import PublishTask, VersionConfirmTask
from release.act import PackageAdmin
from core.common import get_result, logger


def format_response(result):
    if result:
        return HttpResponse(json.dumps(result))
    else:
        return HttpResponse(json.dumps(get_result(1, 'error request')))


class TestAdmin(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        return HttpResponse('this is get method')

    def post(self, request, *args, **kwargs):
        return HttpResponse('this is post method')


class BaseViewAdmin(APIView):
    http_method_names = ['post']
    permission_classes = (permissions.IsAuthenticated,)

    def init(self, request):
        pass

    def run(self):
        pass

    def post(self, request, *args, **kwargs):
        self.init(request)
        return format_response(self.run())

    def get(self, request, *args, **kwargs):
        return self.post(request)


class MissionBaseViewAdmin(BaseViewAdmin):
    creator = 'anonymous'
    item, version, admin = None, None, None

    def init(self, request):
        super(MissionBaseViewAdmin, self).init(request)
        self.item = request.POST.get('item')
        self.version = request.POST.get('version')
        if 'creator' in request.POST:
            self.creator = request.POST.get('creator')
        self.admin = MissionAct(self.item, self.version, creator=self.creator)


class MissionCreateExpandViewAdmin(MissionBaseViewAdmin):
    def init(self, request):
        super(MissionCreateExpandViewAdmin, self).init(request)
        self.item = request.POST.get('item')
        self.version = request.POST.get('version')
        if 'creator' in request.POST:
            self.creator = request.POST.get('creator')
        self.data = request.POST.get('data')
        self.admin = MissionAct(self.item, self.version, creator=self.creator, mock_data=(ast.literal_eval(self.data), {'count': 0, 'results': {}}))

    def run(self):
        return self.admin.create_expand()


class MissionCreateStgViewAdmin(MissionBaseViewAdmin):
    def run(self):
        return self.admin.create_stg()


class MissionCreateProViewAdmin(MissionBaseViewAdmin):
    def run(self):
        return self.admin.create_pro()


class MissionCreateRollViewAdmin(MissionBaseViewAdmin):
    def run(self):
        return self.admin.create_roll()


class MissionJobBaseViewAdmin(BaseViewAdmin):
    mission, admin = None, None

    def init(self, request):
        super(MissionJobBaseViewAdmin, self).init(request)
        self.mission = request.POST.get('mission')
        self.admin = MissionJobAct(self.mission)


class MissionJobCompleteViewAdmin(MissionJobBaseViewAdmin):
    def run(self):
        return self.admin.complete()


class MissionJobResetViewAdmin(MissionJobBaseViewAdmin):
    def run(self):
        return self.admin.reset()


class MissionJobRedoViewAdmin(MissionJobResetViewAdmin):
    def run(self):
        mission = Mission.objects.get(mark=self.mission)
        if mission:
            mission.status = 0
            mission.save()
        else:
            get_result(1, 'error mission id %s ' % self.mission)
        return super(MissionJobRedoViewAdmin, self).run()


class MissionJobCancelViewAdmin(MissionJobBaseViewAdmin):
    def run(self):
        return self.admin.cancel()


class ProgressBaseViewAdmin(BaseViewAdmin):
    mission = None

    def init(self, request):
        if request.method == 'GET':
            self.mission = request.GET.get('mission')
        elif request.method == 'POST':
            self.mission = request.POST.get('mission')
        super(ProgressBaseViewAdmin, self).init(request)


class ProgressGetViewAdmin(ProgressBaseViewAdmin):
    http_method_names = ['post', 'get']

    def run(self):
        return ProgressAct(self.mission).get()


class ProgressRebuildViewAdmin(ProgressBaseViewAdmin):
    def run(self):
        return ProgressAct(self.mission).rebuild()


class ProgressRunViewAdmin(ProgressBaseViewAdmin):
    host, status = None, None

    def init(self, request, *args, **kwargs):
        super(ProgressRunViewAdmin, self).init(request)
        self.host = request.POST.get('host')
        self.status = request.POST.get('status')

    def run(self):
        return ProgressActAdmin().progress_run(self.mission, self.host, self.status)


class ProgressOneViewAdmin(ProgressBaseViewAdmin):
    host, order = None, None

    def init(self, request, *args, **kwargs):
        super(ProgressOneViewAdmin, self).init(request)
        self.host = request.POST.get('host')
        self.order = request.POST.get('order')

    def run(self):
        return ProgressActAdmin().progress_one(self.mission, self.host, self.order)


class WorkFlowAdminView(BaseViewAdmin):
    def post(self):
        return PackageAdmin().run()

    def get(self):
        pass


class PackageAdminView(BaseViewAdmin):
    def init(self, request):
        super(PackageAdminView, self).init(request)
        self.app = request.POST.get('app')
        self.version = request.POST.get('version')

    def run(self):
        if self.app and self.version:
            return PackageAdmin(self.app, self.version).run()
        else:
            return get_result(1, 'app and version not provide')


@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated, ])
@csrf_exempt
def workflow_get_view(req):
    result = None
    if req.method == 'GET':
        if req.GET.has_key('id'):
            id = req.GET.get('id')
            result = workflow_get(id=id)
        else:
            result = workflow_get()
    elif req.method == 'POST':
        new_data = req.POST.get('params')
        result = workflow_update(json.loads(new_data))
    return format_response(result)


class PublishTaskViewAdmin(BaseViewAdmin):
    exec_id = None
    roll = False

    def init(self, request):
        super(PublishTaskViewAdmin, self).init(request)
        self.exec_id = request.POST.get('exec_id')
        if request.POST.get("roll") == "1":
            self.roll = True

    def run(self):
        return PublishTask(self.exec_id, roll=self.roll).run()


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
def mission_exec_status_view(req):
    id = req.GET.get('id')
    content = req.GET.get('content')
    return format_response(mission_exec_status(id, content))


class VersionConfirmTaskViewAdmin(BaseViewAdmin):
    http_method_names = ['GET']
    mission_id = None

    def init(self, request):
        super(VersionConfirmTaskViewAdmin, self).init(request)
        self.mission_id = request.GET.get('mission')

    def run(self):
        return VersionConfirmTask().run(self.mission_id)
