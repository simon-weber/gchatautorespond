from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from .apps.autorespond import urls as autorespond_urls

urlpatterns = [
    url(r'^autorespond/', include(autorespond_urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    # post-login will redirect here.
    url(r'^accounts/profile/$', RedirectView.as_view(pattern_name='autorespond', permanent=False)),

    url(r'^$', RedirectView.as_view(pattern_name='autorespond', permanent=False)),
]
