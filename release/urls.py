from release import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'step', views.StepViewSet)
router.register(r'type', views.TypeViewSet)
router.register(r'status', views.StatusViewSet)
router.register(r'type_detail', views.TypeStepViewSet)
router.register(r'mission', views.ReleaseMissionSet)
router.register(r'expand_mission', views.ExpandMissionSet)
router.register(r'progress', views.ProgressViewSet)
router.register(r'log_progress', views.LogProgressViewSet)
router.register(r'mission_control', views.MissionControlViewSet)

urlpatterns = router.urls
