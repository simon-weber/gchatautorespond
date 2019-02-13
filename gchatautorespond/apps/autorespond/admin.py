from django.conf.urls import url
from django.contrib import admin
from django.http import JsonResponse

from .views import _send_to_worker

from .models import AutoResponse, GoogleCredential

admin.site.register(GoogleCredential)


@admin.register(AutoResponse)
class ResponseAdmin(admin.ModelAdmin):
    def get_urls(self):
        urls = super(ResponseAdmin, self).get_urls()
        my_urls = [
            url(r'^worker/$', self.admin_site.admin_view(self.worker_status)),
            url(r'^worker/stop/(\d+)/$', self.admin_site.admin_view(self.worker_stop)),
            url(r'^worker/restart/(\d+)/$', self.admin_site.admin_view(self.worker_restart)),
        ]
        return my_urls + urls

    def worker_status(self, request):
        res = _send_to_worker('get', '/status')

        # add in additional context
        res_data = res.json()
        bot_ids = res_data.pop('bots')
        autoresponds = AutoResponse.objects.filter(id__in=bot_ids).select_related('user')

        res_data['bot_details'] = sorted(
            [{'ar_id': ar.id,
              'user_email': ar.user.email,
              'is_trial': ar.user.currentlicense.license.is_trial,
              } for ar in autoresponds],
            key=lambda d: d['ar_id'],
        )
        res_data['admin_actions'] = {
            'stop': 'stop/...',
            'restart': 'restart/...',
        }
        return JsonResponse(res_data)

    # these are vulnerable to csrf, but admins are authed rarely and an attacker would need to brute force ids
    def worker_stop(self, request, autorespond_id):
        res = _send_to_worker('post', "/stop/%s" % autorespond_id)
        if res.status_code != 200:
            return JsonResponse({'code': res.status_code})

        return JsonResponse(res.json())

    def worker_restart(self, request, autorespond_id):
        res = _send_to_worker('post', "/restart/%s" % autorespond_id)
        return JsonResponse(res.json())
