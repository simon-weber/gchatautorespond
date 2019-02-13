from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'auth/$', views.auth_view, name='auth_view'),
    url(r'oauth2callback/$', views.auth_return_view),
    url(r'worker_status/$', views.worker_status_view),
    url(r'test/$', views.test_view, name='test_view'),
    url(r'$', views.autorespond_view, name='autorespond'),
]
