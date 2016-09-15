from django.contrib.auth.models import User
from django.db import models


class Message(models.Model):
    """私信"""
    src = models.ForeignKey(User)
    dest = models.ForeignKey(User)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_created=True)


class Topic(models.Model):
    """论坛主题"""
    author = models.ForeignKey(User)
    title = models.CharField(max_length=128)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_created=True)
    like = models.IntegerField()


class Reply(models.Model):
    """回复"""
    author = models.ForeignKey(User)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_created=True)
    highlighted = models.BooleanField(default=False)  # 精华
    stick = models.BooleanField(default=False)  # 置顶
