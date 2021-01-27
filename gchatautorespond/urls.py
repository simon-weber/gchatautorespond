from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from registration.backends.default.views import RegistrationView
from registration.forms import RegistrationFormTermsOfService as RegTOS

from .apps.autorespond import urls as autorespond_urls
from .apps.licensing import urls as licensing_urls
from .apps.autorespond.views import LoggedOutView, PrivacyView, TermsView, ServiceSupportView
from .apps.autorespond import views

urlpatterns = [
    url(r'^autorespond/', include(autorespond_urls)),
    url(r'^payment/', include(licensing_urls)),

    # Override default login to redirect if already logged in.
    # TODO do this for signup as well?
    url(r'^accounts/login', views.login),

    url(r'^admin/', admin.site.urls),

    # Override the default registration form.
    url(r'^accounts/register/$', RegistrationView.as_view(form_class=RegTOS), name='registration_register'),
    url(r'^accounts/', include('registration.backends.default.urls')),

    url(r'^accounts/', include('django.contrib.auth.urls')),

    # post-login will redirect here.
    url(r'^accounts/profile/$', RedirectView.as_view(pattern_name='autorespond', permanent=False)),

    url(r'^privacy/$', PrivacyView.as_view(), name='privacy'),
    url(r'^terms/$', TermsView.as_view(), name='terms'),
    url(r'^services/$', ServiceSupportView.as_view(), name='service_support'),
    url(r'^$', LoggedOutView.as_view(), name='logged_out'),
]
