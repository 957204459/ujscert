# coding=utf-8
from __future__ import unicode_literals

import hashlib
import os
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms import forms

STATUS_UNVERIFIED = 0
STATUS_CONFIRMED = 1
STATUS_IGNORED = 2
STATUS_TO_REVIEW = 3
STATUS_FIXED = 4
STATUS_OPEN = 5

STATUS_CHOICES = (
    (STATUS_UNVERIFIED, '待审核'),  # 漏洞已提交等待审核
    (STATUS_CONFIRMED, '已确认'),  # 漏洞已审核等待处理
    (STATUS_IGNORED, '已忽略'),  # 漏洞不符合要求, 不存在或者已知
    (STATUS_TO_REVIEW, '待复核'),  # 等待提交者复查
    (STATUS_FIXED, '已修复'),  # 修复完成
    (STATUS_OPEN, '已公开'),  # 社区可见
)

TIMELINE_CHANGE_STATUS = 0
TIMELINE_BOUNTY = 1

TIMELINE_CHOICES = (
    (TIMELINE_CHANGE_STATUS, '更新状态'),
    (TIMELINE_BOUNTY, '奖励变动'),
)


def attachment_name(instance, filename):
    date = datetime.now().strftime('%Y-%m-%d')
    name, ext = os.path.splitext(filename)
    new_name = instance.uuid + ext.lower()
    return os.path.join('uploads', date, new_name)


class Vul(models.Model):
    """漏洞"""
    title = models.CharField(max_length=32)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)  # 序列号
    category = models.IntegerField(choices=getattr(settings, 'VUL_TYPE_CHOICES'))
    anonymous = models.BooleanField(default=False)
    detail = models.TextField(max_length=2048)
    attachment = models.FileField(blank=True, upload_to=attachment_name)  # 附件

    status = models.IntegerField(choices=STATUS_CHOICES, default=0)  # 漏洞状态
    submitted = models.DateTimeField(auto_now_add=True, blank=True)  # 提交时间
    confirmed = models.DateTimeField(blank=True, null=True)  # 确认时间
    fixed = models.DateTimeField(blank=True, null=True)  # 修复时间
    score = models.IntegerField(blank=True, default=0,
                                validators=[MaxValueValidator(10), MinValueValidator(0)])  # 评分

    response = models.TextField(blank=True, max_length=512)  # 回复

    def __str__(self):
        return self.title


@receiver(post_save, sender=User)
def add_white_hat(sender, instance, **kwargs):
    if kwargs.get('created'):
        WhiteHat(user=instance).save()


@receiver(post_delete, sender=Vul)
def attachment_delete(sender, instance, **kwargs):
    instance.attachment.delete(False)


class WhiteHat(models.Model):
    """白帽子"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True, null=True)
    bio = models.CharField(max_length=200, blank=True, null=True)
    reputation = models.IntegerField(default=0)
    reports = models.IntegerField(default=0)
    site = models.CharField(max_length=100, default='http://', blank=True, null=True)
    public = models.BooleanField(default=False)

    @property
    def avatar(self):
        avatar_hash = hashlib.md5(self.user.email.lower().encode('utf8')).hexdigest()
        return "https://cn.gravatar.com/avatar/%s" % avatar_hash

    def __str__(self):
        return self.user.username


class AnonymousVul(Vul):
    ip = models.GenericIPAddressField()
    email = models.EmailField(blank=True, null=True)
    anonymous = True


class MemberVul(Vul):
    """会员提交漏洞"""
    author = models.ForeignKey(WhiteHat)
    anonymous = False


@receiver(post_delete, sender=MemberVul)
@receiver(post_save, sender=MemberVul)
def update_score(sender, instance, **kwargs):
    whitehat = WhiteHat.objects.get(pk=instance.author_id)
    vuls = MemberVul.objects.filter(author=whitehat)
    whitehat.reputation = vuls.aggregate(Sum('score')).get('score__sum')
    whitehat.reports = vuls.count()
    whitehat.save()


def image_name(instance, filename):
    date = datetime.now().strftime('%Y-%m-%d')
    name, ext = os.path.splitext(filename)
    filename = uuid.uuid1().hex + ext.lower()
    return os.path.join('images', date, filename)


class Image(models.Model):
    img = models.ImageField(upload_to=image_name)
    timestamp = models.DateTimeField(auto_now_add=True, blank=True)

    def clean_img(self):
        image = self.cleaned_data.get('img')
        if not image:
            raise forms.ValidationError('图片不合法')

        main, sub = image.content_type.split('/')
        if not (main == 'image' and sub.lower() in ['jpeg', 'pjpeg', 'png', 'jpg']):
            raise forms.ValidationError('图片不合法')

        if len(image) > 1024 * 1024:  # max: 1M
            raise forms.ValidationError('文件尺寸太大')

        return image

    def __str__(self):
        return '%s (%d x %d)' % (self.img.path, self.img.width, self.img.height)


@receiver(post_delete, sender=Image)
def image_delete(sender, instance, **kwargs):
    instance.img.delete(False)


class Invitation(models.Model):
    """邀请码"""
    email = models.EmailField(blank=True, null=True)
    code = models.UUIDField(default=uuid.uuid4, editable=False)
    valid = models.BooleanField(default=True)
    expired = models.DateTimeField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s' % (self.code, self.email)


class Timeline(models.Model):
    """事件"""
    vul = models.ForeignKey(Vul)
    event_type = models.IntegerField(choices=TIMELINE_CHOICES, default=TIMELINE_CHANGE_STATUS)
    extra = JSONField(default={})
    timestamp = models.DateTimeField(auto_created=True, auto_now_add=True)
    comment = models.CharField(max_length=1024)

    def __str__(self):
        return self.comment


class Comment(models.Model):
    author = models.ForeignKey(WhiteHat)
    vul = models.ForeignKey(Vul)
    timestamp = models.DateTimeField(auto_created=True, auto_now_add=True)
    content = models.CharField(max_length=1024)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return '%s: %s' % (self.author.user.username, self.content)


class LikeForComment(models.Model):
    author = models.ForeignKey(WhiteHat)
    timestamp = models.DateTimeField(auto_created=True, auto_now_add=True)
    comment = models.ForeignKey(Comment)

    def __str__(self):
        comment = self.comment.content
        max_len = 100
        if len(comment) > max_len:
            comment = comment[0:max_len] + '...'
        return '%s liked "%s"' % (self.author.user.username, comment)


class Income(models.Model):
    """积分变动"""
    user = models.ForeignKey(User)
    cost = models.IntegerField()  # 正为奖励, 负为消费
    reason = models.CharField(max_length=256)
    timestamp = models.DateTimeField(auto_created=True)

    def __str__(self):
        return '%s %d' % (self.user.username, self.cost)


class Reward(models.Model):
    title = models.CharField(max_length=64) # 名字
    intro = models.TextField(blank=True, max_length=200)  # 简介
    img = models.ImageField(upload_to=image_name, default='')  # 图片
    price = models.IntegerField()  # 售价
    purchased = models.IntegerField()  # 已兑换
    available = models.IntegerField()  # 余量

    def __str__(self):
        return self.title
