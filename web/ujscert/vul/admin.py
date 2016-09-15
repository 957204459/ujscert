from django.contrib import admin

from django.forms import Textarea
from ujscert.vul.models import *


@admin.register(Image, WhiteHat, Invitation)
class Admin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
            attrs={'rows': 8,
                   'cols': 40})},
    }


@admin.register(Vul, AnonymousVul, MemberVul)
class VulAdmin(admin.ModelAdmin):
    list_filter = ('status', 'category')
