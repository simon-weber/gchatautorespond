import logging

from apiclient.discovery import build
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.utils.encoding import smart_str
from django.core.mail import mail_admins
import httplib2
from oauth2client import xsrfutil
from oauth2client.client import flow_from_clientsecrets
from django.forms.models import modelformset_factory
from django.template.context_processors import csrf
from django.conf import settings

from .models import GoogleCredential, AutoResponse
from gchatautorespond.lib.chatworker import Worker, WorkerUpdate

FLOW = flow_from_clientsecrets(
    settings.CLIENT_SECRETS_PATH,
    scope=settings.OAUTH_SCOPE,
    redirect_uri=settings.OAUTH_REDIRECT_URI)

_AutoResponseFormSet = modelformset_factory(
    AutoResponse,
    fields=('response', 'credentials', 'email_notifications'),
    can_delete=True)

logger = logging.getLogger(__name__)


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


def autorespond_view(request):
    """List/update accounts and autoresponses."""

    if not request.user.is_authenticated():
        return render_to_response('logged_out.html')

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
            updates = []
            for autorespond in formset.deleted_objects:
                updates.append(WorkerUpdate(autorespond.id, stop=True))
                autorespond.delete()

            for autorespond in autoresponds:
                autorespond.user = request.user
                autorespond.save()
                updates.append(WorkerUpdate(autorespond.id, stop=False))

            if updates:
                Worker.QueueManager.register('get_queue')
                manager = Worker.QueueManager(address=('', 50000), authkey=settings.QUEUE_AUTH_KEY)
                manager.connect()  # TODO errno 61 if worker not running
                queue = manager.get_queue()
                for update in updates:
                    queue.put_nowait(update)

                mail_admins(
                    "autoresponses changed by %s" % request.user.username,
                    "There were %s updates." % len(updates),
                    fail_silently=True)

            return redirect(autorespond_view)
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
        return HttpResponseBadRequest()

    credential = FLOW.step2_exchange(request.GET)

    if credential.refresh_token is not None:
        # refresh tokens only come with fresh auths.
        # we don't want to store reauths, since we'd clobber the refresh token.
        http = httplib2.Http()
        http = credential.authorize(http)
        service = build("plus", "v1", http=http)
        res = service.people().get(userId='me').execute()

        email = res['emails'][0]['value']

        GoogleCredential.objects.update_or_create(
            email=email, user=request.user,
            defaults={'credentials': credential})

    return redirect(autorespond_view)
