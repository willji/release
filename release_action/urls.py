from django.conf.urls import url
from release_action import views
from release_action.views import *
from release import act
urlpatterns = [
    url(r'^mission/exec/run', PublishTaskViewAdmin.as_view()),
    url(r'^mission/exec/status', views.mission_exec_status_view),
    url(r'^mission/create/expand', MissionCreateExpandViewAdmin.as_view()),
    url(r'^mission/create/stg', MissionCreateStgViewAdmin.as_view()),
    url(r'^mission/create/pro', MissionCreateProViewAdmin.as_view()),
    url(r'^mission/create/roll', MissionCreateRollViewAdmin.as_view()),
    url(r'^mission/complete', MissionJobCompleteViewAdmin.as_view()),
    url(r'^mission/version/confirm', VersionConfirmTaskViewAdmin.as_view()),
    url(r'^mission/reset', MissionJobResetViewAdmin.as_view()),
    url(r'^mission/redo', MissionJobRedoViewAdmin.as_view()),
    url(r'^mission/cancel', MissionJobCancelViewAdmin.as_view()),
    url(r'^progress/get', ProgressGetViewAdmin.as_view()),
    url(r'^progress/rebuild', ProgressRebuildViewAdmin.as_view()),
    url(r'^progress/run', ProgressRunViewAdmin.as_view()),
    url(r'^progress/one', ProgressOneViewAdmin.as_view()),
    url(r'^workflow', views.workflow_get_view),
    url(r'^test', TestAdmin.as_view()),
    url(r'^package', PackageAdminView.as_view()),

]
