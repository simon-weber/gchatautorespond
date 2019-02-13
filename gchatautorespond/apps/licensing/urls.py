from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'detail/$', views.details_view, name='license_details'),
    url(r'cancel/$', views.cancel_view, name='license_cancel'),
]
