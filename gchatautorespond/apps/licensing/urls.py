from django.conf.urls import url

urlpatterns = [
    url(r'detail/$', 'gchatautorespond.apps.licensing.views.details_view', name='license_details'),
    url(r'cancel/$', 'gchatautorespond.apps.licensing.views.cancel_view', name='license_cancel'),
]
