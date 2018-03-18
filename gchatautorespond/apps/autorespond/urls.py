from django.conf.urls import url

urlpatterns = [
    url(r'auth/$', 'gchatautorespond.apps.autorespond.views.auth_view'),
    url(r'oauth2callback/$', 'gchatautorespond.apps.autorespond.views.auth_return_view'),
    url(r'worker_status/$', 'gchatautorespond.apps.autorespond.views.worker_status_view'),
    url(r'test/$', 'gchatautorespond.apps.autorespond.views.test_view'),
    url(r'$', 'gchatautorespond.apps.autorespond.views.autorespond_view', name='autorespond'),
]
