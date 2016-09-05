from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView

from .apps.autorespond import urls as autorespond_urls
from .apps.autorespond.views import LoggedOutView, PrivacyView

urlpatterns = [
    url(r'^autorespond/', include(autorespond_urls)),

    # Override default login to redirect if already logged in.
    # TODO do this for signup as well?
    url(r'^accounts/login', 'gchatautorespond.apps.autorespond.views.login'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    # post-login will redirect here.
    url(r'^accounts/profile/$', RedirectView.as_view(pattern_name='autorespond', permanent=False)),

    url(r'^privacy/$', PrivacyView.as_view(), name='privacy'),
    url(r'^$', LoggedOutView.as_view(), name='logged_out'),
]
