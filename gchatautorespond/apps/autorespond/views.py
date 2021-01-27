import logging

from apiclient.discovery import build
from concurrent.futures import ThreadPoolExecutor
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.utils.decorators import method_decorator
from django.db import IntegrityError
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.utils.encoding import smart_str
import httplib2
import oauth2client.contrib.xsrfutil as xsrfutil
from oauth2client.client import flow_from_clientsecrets
from django.contrib.auth import views as auth_views
from django.forms.models import modelformset_factory
from django.conf import settings
from django.views.generic import TemplateView
from django.forms.formsets import DELETION_FIELD_NAME
import requests

from .models import GoogleCredential, AutoResponse, ExcludedUser
from gchatautorespond.apps.licensing.models import License
from gchatautorespond.lib import report_ga_event_async

FLOW = flow_from_clientsecrets(
    settings.GOOGLE_OAUTH2_CLIENT_SECRETS_JSON,
    scope=settings.OAUTH_SCOPE,
    redirect_uri=settings.OAUTH_REDIRECT_URI)

_AutoResponseFormSet = modelformset_factory(
    AutoResponse,
    fields=('response', 'credentials', 'email_notifications', 'throttle_mins', 'status_detection', 'disable_responses'),
    can_delete=True)

_ExcludedUserFormSet = modelformset_factory(
    ExcludedUser,
    fields=('autorespond', 'name', 'email_notifications'),
    labels={'autorespond': 'Autorespond account'},
    extra=1,
    can_delete=True)

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(4)


def _send_to_worker(verb, url):
    method = getattr(requests, verb)
    return method("http://127.0.0.1:%s%s" % (settings.WORKER_PORT, url))


def _request_test_message(email):
    return requests.post("http://127.0.0.1:%s/message/%s" % (settings.TESTWORKER_PORT, email))


class ExcludedUserFormSet(_ExcludedUserFormSet):
    def __init__(self, autoresponds, *args, **kwargs):
        self.autoresponds = autoresponds
        super(ExcludedUserFormSet, self).__init__(*args, **kwargs)
        self.prefix = 'excluded'

    def _construct_form(self, i, **kwargs):
        form = super(ExcludedUserFormSet, self)._construct_form(i, **kwargs)
        form.fields['autorespond'].queryset = self.autoresponds
        form.fields['autorespond'].label_from_instance = lambda obj: obj.credentials.email

        if form.empty_permitted:
            # Don't show the delete field for empty forms.
            del form.fields[DELETION_FIELD_NAME]

        return form


class AutoResponseFormSet(_AutoResponseFormSet):
    def __init__(self, credentials, *args, **kwargs):
        self.credentials = credentials

        # There can only be 1 response per credential.
        # This prevents showing more empty forms if all are filled in.
        self.max_num = len(credentials)
        self.extra = 1

        super(AutoResponseFormSet, self).__init__(*args, **kwargs)
        self.active_credentials = []
        if self.queryset:
            self.active_credentials = [autorespond.credentials for autorespond in self.queryset]
        self.prefix = 'autorespond'

    def _construct_form(self, i, **kwargs):
        form = super(AutoResponseFormSet, self)._construct_form(i, **kwargs)
        form.fields['credentials'].queryset = self.credentials
        form.fields['credentials'].label_from_instance = lambda obj: obj.email

        if form.empty_permitted:
            del form.fields[DELETION_FIELD_NAME]

        return form


@method_decorator(cache_control(public=True, max_age=3600), name='dispatch')
class LoggedOutView(TemplateView):
    price = settings.PRICE_REPR
    trial_length = "%s day" % License.TRIAL_LENGTH.days

    template_name = 'logged_out.html'


# TODO these shouldn't show the logged-in navbar so they can be cached
class PrivacyView(TemplateView):
    template_name = 'privacy.html'


class TermsView(TemplateView):
    template_name = 'terms.html'


class ServiceSupportView(TemplateView):
    template_name = 'service_support.html'


def login(request):
    """Default login, but redirect if we're already logged in."""

    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)

    return auth_views.LoginView.as_view()(request)


@login_required
def test_view(request):
    """Send a test message to an active autoresponder."""

    autoresponds = AutoResponse.objects.filter(user=request.user)

    if request.method == 'POST':
        email = request.POST.get("email")
        if email in [autorespond.credentials.email for autorespond in autoresponds]:
            try:
                _request_test_message(email)
                messages.success(request, 'Successfully sent a test message.')
                report_ga_event_async(email, category='autoresponse', action='test', label='success')
            except:
                logger.exception('failed to send test message')
                messages.error(request, 'Failed to send a test message.')
                report_ga_event_async(email, category='autoresponse', action='test', label='failure')

            return redirect('autorespond')
    return HttpResponseBadRequest()


def autorespond_view(request):
    """List/update accounts and autoresponses."""

    if not request.user.is_authenticated:
        return redirect('logged_out')

    gcredentials = GoogleCredential.objects.filter(user=request.user)
    autoresponds = AutoResponse.objects.filter(user=request.user)
    excludeds = ExcludedUser.objects.filter(autorespond__user=request.user)
    license = request.user.currentlicense.license

    if request.method == 'GET':
        autorespond_formset = AutoResponseFormSet(credentials=gcredentials, queryset=autoresponds)
        excluded_formset = ExcludedUserFormSet(autoresponds=autoresponds, queryset=excludeds)

        c = {
            'user': request.user,
            'is_active': license.is_active,
            'gcredentials': gcredentials,
            'autorespond_formset': autorespond_formset,
            'excluded_formset': excluded_formset,
        }

        return render(request, 'logged_in.html', c)

    elif request.method == 'POST':
        autorespond_formset = AutoResponseFormSet(gcredentials, request.POST)
        excluded_formset = ExcludedUserFormSet(autoresponds, request.POST)

        if request.POST.get("submit_autoresponses") and autorespond_formset.is_valid():
            autoresponds = autorespond_formset.save(commit=False)   # save_m2m if add many 2 many
            for autorespond in autorespond_formset.deleted_objects:
                thread_pool.submit(_send_to_worker, 'post', "/stop/%s" % autorespond.id)
                autorespond.delete()
                report_ga_event_async(autorespond.credentials.email, category='autoresponse', action='delete')

            for autorespond in autoresponds:
                autorespond.user = request.user
                autorespond.save()
                thread_pool.submit(_send_to_worker, 'post', "/restart/%s" % autorespond.id)
                report_ga_event_async(autorespond.credentials.email, category='autoresponse', action='upsert')

            return redirect('autorespond')
        elif request.POST.get("submit_excludeds") and excluded_formset.is_valid():
            excludeds = excluded_formset.save(commit=False)   # save_m2m if add many 2 many
            restart_ids = set()
            for excluded in excluded_formset.deleted_objects:
                restart_ids.add(excluded.autorespond.id)
                excluded.delete()
                report_ga_event_async(excluded.autorespond.credentials.email, category='excluded', action='delete')

            for excluded in excludeds:
                restart_ids.add(excluded.autorespond.id)
                excluded.save()
                report_ga_event_async(excluded.autorespond.credentials.email, category='excluded', action='upsert')

            for restart_id in restart_ids:
                thread_pool.submit(_send_to_worker, 'post', "/restart/%s" % restart_id)

            return redirect('autorespond')
        else:
            # Don't use the empty submitted data for the other form.
            if request.POST.get("submit_excludeds"):
                autorespond_formset = AutoResponseFormSet(credentials=gcredentials, queryset=autoresponds)
            elif request.POST.get("submit_autoresponses"):
                excluded_formset = ExcludedUserFormSet(autoresponds=autoresponds, queryset=excludeds)

            c = {
                'user': request.user,
                'is_active': license.is_active,
                'gcredentials': gcredentials,
                'autorespond_formset': autorespond_formset,
                'excluded_formset': excluded_formset,
            }

            return render(request, 'logged_in.html', c, status=400)
    else:
        return HttpResponseBadRequest()


def worker_status_view(request):
    """Show the status of the worker."""

    res = _send_to_worker('get', '/status')
    return JsonResponse(res.json())


@login_required
def auth_view(request):
    """Start an oauth flow."""

    FLOW.params['state'] = xsrfutil.generate_token(settings.SECRET_KEY,
                                                   request.user)

    # If we lose a refresh token at some point, this will allow a re-auth to give us one.
    FLOW.params['approval_prompt'] = 'force'

    authorize_url = FLOW.step1_get_authorize_url()
    return HttpResponseRedirect(authorize_url)


@login_required
def auth_return_view(request):
    """Receive a successful oauth flow."""

    token = str(request.GET['state']).encode()
    if not xsrfutil.validate_token(settings.SECRET_KEY, token, request.user):
        return HttpResponseBadRequest('Improper OAuth request.')

    if 'error' in request.GET:
        if request.GET['error'] != 'access_denied':
            # access_denied means the user clicked deny; it's not exceptional.
            logger.error("error on oauth return: %s", request.GET['error'])
        return redirect('autorespond')

    credential = FLOW.step2_exchange(request.GET)

    if credential.refresh_token is not None:
        # refresh tokens only come with fresh auths.
        # we don't want to store reauths, since we'd clobber the refresh token.
        http = httplib2.Http()
        http = credential.authorize(http)
        # https://github.com/googleapis/google-api-python-client/issues/299
        service = build("oauth2", "v2", http=http, cache_discovery=False)
        res = service.userinfo().get().execute()

        email = res['email']

        try:
            GoogleCredential.objects.update_or_create(
                email=email, user=request.user,
                defaults={'credentials': credential})
        except IntegrityError:
            logger.error('attempt to connect already-connected account %r to %r',
                         email, request.user.email,
                         extra={'tags': {'linker': request.user.email,
                                         'linkee': email}})

            return HttpResponseBadRequest('This Google account is already connected to a different account.')

    return redirect('autorespond')
