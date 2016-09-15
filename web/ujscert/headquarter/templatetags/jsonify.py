from django import template
from django.utils.safestring import mark_safe
import ujson

register = template.Library()


@register.filter
def jsonify(o):
    return mark_safe(ujson.dumps(o))
