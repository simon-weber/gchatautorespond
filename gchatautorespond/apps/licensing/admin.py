from django.contrib import admin

from .models import License, CurrentLicense

admin.site.register(License)
admin.site.register(CurrentLicense)
