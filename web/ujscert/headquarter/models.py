import uuid

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from djorm_pgfulltext.fields import VectorField
from djorm_pgfulltext.models import SearchManager

from ujscert.headquarter.utils import gen_cert


class Agent(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100, blank=True)
    x509_cert = models.TextField(blank=True)
    x509_key = models.TextField(blank=True)

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Agent)
def pre_save_hook(sender, instance, **kwargs):
    if len(instance.x509_cert) == 0:
        instance.x509_cert, instance.x509_key = gen_cert(instance.uid)


class Property(models.Model):
    ip = models.GenericIPAddressField()
    name = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=40, blank=True)
    description = models.TextField(blank=True)


class Website(models.Model):
    domain = models.CharField(max_length=64)
    ip = models.GenericIPAddressField()
    port = models.IntegerField(default=80)
    title = models.TextField(blank=True)

    url = models.CharField(max_length=512)
    headers = JSONField(default={})
    raw_headers = models.TextField(blank=True)
    html = models.TextField()  # full html source
    app_joint = models.CharField(max_length=256, default='')  # ' '.join(apps), for full search

    timestamp = models.DateTimeField(auto_now=True)

    search_index = VectorField(db_index=False)
    objects = SearchManager(
        fields=('domain', 'url', 'raw_headers', 'app_joint', 'html', 'title'),
        config='chinese',
        search_field='search_index',
        auto_update_search_field=True
    )

    def __str__(self):
        return self.title


class App(models.Model):
    website = models.ForeignKey(Website)
    app = models.CharField(max_length=32)
    ver = models.CharField(max_length=64)
    versions = ArrayField(models.CharField(max_length=64), default=[])

    def __str__(self):
        return '%s: %s' % (self.app, self.ver)


class Fingerprint(models.Model):
    ip = models.GenericIPAddressField()
    port = models.PositiveIntegerField()
    service = models.CharField(max_length=64, blank=True)

    os = models.CharField(max_length=32, blank=True)
    info = models.CharField(max_length=256, blank=True)
    product = models.CharField(max_length=256, blank=True)
    hostname = models.CharField(max_length=128, blank=True)
    device = models.CharField(max_length=128, blank=True)
    version = models.CharField(max_length=128, blank=True)
    cpes = ArrayField(models.CharField(max_length=128), default=[])

    certificate = JSONField(default={})
    banner = models.TextField()
    raw = models.TextField()

    timestamp = models.DateTimeField(auto_now=True)

    search_index = VectorField(db_index=False)
    objects = SearchManager(
        fields=('os', 'info', 'service', 'product', 'hostname', 'device', 'version', 'banner'),
        config='chinese',
        search_field='search_index',
        auto_update_search_field=True
    )

    def __str__(self):
        return '%s:%d' % (self.ip, self.port)


class Alert(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField(blank=True)
    source = models.CharField(max_length=16, blank=True)
    url = models.CharField(max_length=1024, unique=True)
    timestamp = models.DateTimeField()
    keywords = ArrayField(models.TextField(max_length=64), default=[], blank=True)
    highlighted = models.BooleanField(default=False)

    def __str__(self):
        return self.title
