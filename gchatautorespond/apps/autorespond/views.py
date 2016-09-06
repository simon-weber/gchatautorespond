import logging

from apiclient.discovery import build
from concurrent.futures import ThreadPoolExecutor
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render_to_response
from django.utils.encoding import smart_str
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from django.contrib.auth.views import login as contrib_login
from django.forms.models import modelformset_factory
from django.template.context_processors import csrf
from django.conf import settings
from django.views.generic import TemplateView
import requests

from .models import GoogleCredential, AutoResponse
from gchatautorespond.lib import report_ga_event_async

FLOW = flow_from_clientsecrets(
    settings.CLIENT_SECRETS_PATH,
    scope=settings.OAUTH_SCOPE,
    redirect_uri=settings.OAUTH_REDIRECT_URI)

_AutoResponseFormSet = modelformset_factory(
    AutoResponse,
    fields=('response', 'credentials', 'email_notifications'),
    can_delete=True)

logger = logging.getLogger(__name__)
thread_pool = ThreadPoolExecutor(4)


def _send_to_worker(verb, url):
    method = getattr(requests, verb)
    return method("http://127.0.0.1:%s%s" % (settings.WORKER_PORT, url))


class AutoResponseFormSet(_AutoResponseFormSet):
    def __init__(self, credentials, *args, **kwargs):
        self.credentials = credentials

        # There can only be 1 response per credential.
        # This prevents showing more forms than needed.
        self.max_num = len(credentials)
        self.extra = len(credentials)

        super(AutoResponseFormSet, self).__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        form = super(AutoResponseFormSet, self)._construct_form(i, **kwargs)
        form.fields['credentials'].queryset = self.credentials
        return form


class LoggedOutView(TemplateView):
    """Display a static about page.

    This should be cached aggressively.
    """

    template_name = 'logged_out.html'


def login(request):
    """Default login, but redirect if we're already logged in."""

    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)

    return contrib_login(request)


def autorespond_view(request):
    """List/update accounts and autoresponses."""

    if not request.user.is_authenticated():
        return redirect('logged_out')

    gcredentials = GoogleCredential.objects.filter(user=request.user)

    if request.method == 'GET':
        autoresponds = AutoResponse.objects.filter(user=request.user)

        formset = AutoResponseFormSet(credentials=gcredentials, queryset=autoresponds)

        c = {
            'user': request.user,
            'gcredentials': gcredentials,
            'autorespond_formset': formset,
        }
        c.update(csrf(request))

        return render_to_response('logged_in.html', c)

    elif request.method == 'POST':
        formset = AutoResponseFormSet(gcredentials, request.POST)
        if formset.is_valid():
            autoresponds = formset.save(commit=False)   # save_m2m if add many 2 many
            for autorespond in formset.deleted_objects:
                thread_pool.submit(_send_to_worker, 'post', "/stop/%s" % autorespond.id)
                autorespond.delete()
                report_ga_event_async(autorespond.credentials.email, category='autoresponse', action='delete')

            for autorespond in autoresponds:
                autorespond.user = request.user
                autorespond.save()
                thread_pool.submit(_send_to_worker, 'post', "/restart/%s" % autorespond.id)
                report_ga_event_async(autorespond.credentials.email, category='autoresponse', action='upsert')

            return redirect('autorespond')
        else:
            c = {
                'user': request.user,
                'gcredentials': gcredentials,
                'autorespond_formset': formset,
            }
            c.update(csrf(request))

            return render_to_response('logged_in.html', c, status=400)
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

    token = smart_str(request.GET['state'])
    if not xsrfutil.validate_token(settings.SECRET_KEY, token, request.user):
        return HttpResponseBadRequest('Improper OAuth request.')

    if 'error' in request.GET:
        logger.error("error on oauth return: %s", request.GET['error'])
        return redirect('autorespond')

    credential = FLOW.step2_exchange(request.GET)

    if credential.refresh_token is not None:
        # refresh tokens only come with fresh auths.
        # we don't want to store reauths, since we'd clobber the refresh token.
        http = httplib2.Http()
        http = credential.authorize(http)
        service = build("plus", "v1", http=http)
        res = service.people().get(userId='me').execute()

        email = res['emails'][0]['value']

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
