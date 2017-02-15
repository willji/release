from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.authtoken import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/token/', views.obtain_auth_token),
    url(r'^api/api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('release.urls')),
    url(r'^', include('release_action.urls')),
]

