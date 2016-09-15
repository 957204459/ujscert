from django.contrib import admin

from ujscert.headquarter.models import Agent, Fingerprint, Website, Alert


class AgentAdmin(admin.ModelAdmin):
    readonly_fields = ('x509_cert', 'x509_key')

admin.site.register(Agent, AgentAdmin)
admin.site.register(Fingerprint)
admin.site.register(Website)
admin.site.register(Alert)
