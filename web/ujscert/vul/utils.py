# coding=utf-8
from os import path

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from ujscert.vul.models import Vul, WhiteHat


def to_review(request):
    context = {}
    if request.user.is_authenticated():
        context.update({'self_profile': WhiteHat.objects.get(user=request.user)})

    if request.user.is_staff:
        context.update({
            'to_be_review': Vul.objects.filter(status=0).count(),
        })

    return context


def customize(request):
    return {
        'site_title': getattr(settings, 'SITE_TITLE'),
        'site_logo': getattr(settings, 'SITE_LOGO'),
        'site_organization': getattr(settings, 'SITE_ORGANIZATION'),
    }


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# todo: async
def send_rendered_mail(address, template_name='invite', args=None):
    if args is None:
        args = {}

    site_title = getattr(settings, 'SITE_TITLE')
    templates = {
        'invite': '注册邀请',
        'ignore': '报告被忽略',
        'submission_alert': '新的漏洞报告',
    }

    if template_name in templates:
        subject = '[%s] %s' % (site_title, templates[template_name])
        msg_plain = render_to_string(path.join('mail', '%s.txt' % template_name), args)
        msg_html = render_to_string(path.join('mail', '%s.html' % template_name), args)

        return send_mail(
            subject,
            msg_plain,
            settings.EMAIL_SENDER,
            [address],
            html_message=msg_html,
            fail_silently=True)

    return 0
