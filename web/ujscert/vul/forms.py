# coding=utf-8
from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import Textarea
from django.forms.widgets import Input, Select
from ujscert.vul.models import AnonymousVul, MemberVul, Image, WhiteHat, Vul, Comment

bs4_form = {'attrs': {'class': 'form-control'}}


def make_captcha():
    return CaptchaField(label='验证码(点击图片刷新)', error_messages={
        'invalid': '验证码错误',
        'required': '验证码不能为空'})


class ReportForm(forms.ModelForm):
    captcha = make_captcha()

    class Meta:
        model = MemberVul
        fields = ('title', 'category', 'detail', 'attachment')
        labels = {
            'title': '漏洞标题',
            'category': '漏洞类型',
            'detail': '漏洞细节',
            'attachment': '附件',
        }

        widgets = {
            'detail': Textarea(**bs4_form),
            'title': Input(**bs4_form),
            'category': Select(**bs4_form),
        }

        error_messages = {
            'title': {
                'required': '标题不能为空',
            },
            'category': {
                'required': '请选择一个分类',
            },
            'detail': {
                'required': '请填写漏洞细节',
            }
        }


class AnonymousReportForm(ReportForm):
    captcha = make_captcha()

    class Meta:
        model = AnonymousVul
        fields = ('title', 'category', 'detail', 'attachment', 'email')
        labels = {
            'title': '漏洞标题',
            'category': '漏洞类型',
            'detail': '漏洞细节',
            'attachment': '附件',
            'email': '注册邮箱(可选)',
        }

        widgets = {
            'detail': Textarea(**bs4_form),
            'title': Input(**bs4_form),
            'category': Select(**bs4_form),
            'email': Input(attrs={
                'class': 'form-control',
                'placeholder': '跟踪漏洞状态并注册为正式用户，内测版仅支持 @ujs.edu.cn 的邮件地址'
            }),
        }


class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = ('img',)


class LoginForm(AuthenticationForm):
    captcha = make_captcha()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = WhiteHat
        fields = ('bio', 'site', 'department', 'public')
        labels = {
            'bio': '一句话简介',
            'department': '部门',
            'site': '个人首页',
            'public': '公开展示个人资料',
        }

        widgets = {
            'bio': Input(**bs4_form),
            'department': Input(**bs4_form),
            'site': Input(**bs4_form),
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Vul
        fields = ('status', 'score', 'response')


class CommentForm(forms.ModelForm):
    captcha = make_captcha()

    class Meta:
        model = Comment
        fields = ('content',)
