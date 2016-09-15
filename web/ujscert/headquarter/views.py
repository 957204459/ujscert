import csv
import ujson

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, Http404
from django.shortcuts import render, redirect
from django.utils.decorators import available_attrs
from django.utils.six import wraps
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from ujscert.headquarter.utils import staff_required, parse_dn, parse_query
from ujscert.headquarter.models import Agent, Fingerprint, Website, App, Alert



def api(func):
    @wraps(func, assigned=available_attrs(func))
    def decorator(request, *args, **kwargs):
        if not getattr(settings, 'DEBUG', False):  # production
            if request.META.get('HTTP_X_VERIFIED') == 'SUCCESS':
                cert_dn = request.META.get('HTTP_X_CERT_DN')
                cert_info = parse_dn(cert_dn)
                try:
                    agent = Agent.objects.get(uid=cert_info.get('CN', ''))
                except ValueError:
                    raise PermissionDenied
                except Agent.DoesNotExist:
                    raise PermissionDenied

                request.META['UID'] = agent.uid
            else:
                return HttpResponse('Unauthorized', status=401)

        return func(request, *args, **kwargs)

    return decorator


@api
@csrf_exempt
@require_http_methods(['PUT'])
def index_alert_view(request):
    try:
        data = ujson.loads(request.body)
        Alert(**data).save()
    except ValueError as e:
        return HttpResponseBadRequest(e)

    response = {'status': 'ok'}
    return JsonResponse(response)


@api
@require_GET
def pong_api_view(request):
    prefix = 'HTTP_'
    headers = dict((header.replace(prefix, ''), value)
                   for header, value in request.META.items() if header.startswith(prefix))
    response = {
        'headers': headers,
        'pong': 'You know, for indexing',
    }
    return JsonResponse(response)


@api
@csrf_exempt
@require_POST
def index_web_api_view(request):
    try:
        data = ujson.loads(request.body)
    except ValueError as e:
        return HttpResponseBadRequest(e)

    if type(data) is list and len(data):
        keys = ['domain', 'ip', 'port', 'url', 'headers', 'html', 'title']

        for item in data:
            kwargs = {key: item.get(key, '') for key in keys}
            kwargs['raw_headers'] = item.get('rawHeader')
            kwargs['app_joint'] = '/'.join(item.get('apps', []))

            if not kwargs['title']:
                kwargs['title'] = kwargs['url']

            website = Website(**kwargs)
            website.save()

            if 'detail' in item:
                for name, app in item['detail'].items():
                    App(app=name, ver=app.get('version'),
                        website=website, versions=app.get('versions')).save()

        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'fail', 'reason': 'invalid input'})


@api
@csrf_exempt
@require_POST
def index_host_api_view(request):
    try:
        data = ujson.loads(request.body)
    except ValueError as e:
        return HttpResponseBadRequest(e)

    if type(data) is list and len(data):
        for item in data:
            Fingerprint(**item).save()
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'fail', 'reason': 'invalid input'})


@api
@require_GET
def apps_api_view(request):
    products = [item['product'] for item in Fingerprint.objects.values('product').distinct()]
    webapps = [item['app'] for item in App.objects.values('app').distinct()]
    return JsonResponse({'apps': products + webapps})


@api
@require_http_methods(["PUT"])
@csrf_exempt
def feed_api_view(request):
    try:
        item = ujson.loads(request.body)
        Alert(**item).save()
    except ValueError as e:
        return HttpResponseBadRequest(e)
    except IntegrityError:
        pass

    return JsonResponse({'status': 'ok'})


@staff_required
@require_GET
def alert_view(request):
    page = request.GET.get('page', 1)

    qs = Alert.objects.all().order_by('-timestamp')
    paginator = Paginator(qs, 10)
    count = qs.count()

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    data = {
        'items': items,
        'count': count,
    }

    return render(request, 'alert_list.html', data)


def search(query, topic):
    dsl = parse_query(query)
    if topic == 'host':
        host_filters = ('os', 'port', 'product', 'service', 'ip', 'hostname', 'device')
        filters = {'%s__iexact' % key: dsl[key] for key in host_filters if key in dsl}
        qs = Fingerprint.objects.filter(**filters).order_by('ip', '-timestamp').distinct('ip')

    else:
        app_filters = ('app', 'ver')
        filters = {'app__%s__iexact' % key: dsl[key] for key in app_filters if key in dsl}

        if 'ip' in dsl:
            filters['ip'] = dsl['ip']

        qs = Website.objects.filter(**filters).prefetch_related('app_set')

    if len(dsl['search']):
        keyword = ' '.join(dsl['search'])
        qs = qs.search(keyword)
        filters['keyword'] = keyword

    return qs, filters


@staff_required
@require_GET
def export_view(request):
    query = request.GET.get('q')
    topic = request.GET.get('t')

    if not query:
        return redirect('search_home')

    if topic not in ('host', 'web'):
        topic = 'host'

    qs, filters = search(query, topic)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    writer = csv.writer(response)

    if topic == 'web':
        writer.writerow(['url', 'title'])
        for record in qs:
            writer.writerow([record.url, record.title])

    else:
        writer.writerow(['ip', 'port', 'service', 'product', 'version', 'os'])
        for record in qs:
            writer.writerow([record.ip, record.port, record.service, record.product, record.version, record.os])

    return response


@staff_required
@require_GET
def search_view(request):
    query = request.GET.get('q')
    page = request.GET.get('page')
    topic = request.GET.get('t')

    if not query:
        return redirect('search_home')

    if topic not in ('host', 'web'):
        topic = 'host'

    qs, filters = search(query, topic)
    if not filters:
        return render(request, 'search_error.html', {'query': query})

    paginator = Paginator(qs, 10)
    count = qs.count()

    try:
        items = paginator.page(page)
    except PageNotAnInteger:
        items = paginator.page(1)
    except EmptyPage:
        items = paginator.page(paginator.num_pages)

    data = {
        'topic': topic,
        'query': query,
        'items': items,
        'count': count,
    }

    return render(request, 'search_result.html', data)


@require_GET
@staff_required
def search_home_view(request):
    data = {field + 's': Fingerprint.objects.values(field).distinct()
            for field in ['port', 'product', 'os', 'device', 'service']}
    data['webapps'] = App.objects.values('app').distinct()
    return render(request, 'search_home.html', data)


@require_GET
@staff_required
def host_view(request, ip):
    results = Fingerprint.objects.filter(ip=ip).order_by('port', '-timestamp').distinct('port')
    data = {
        'ip': ip,
        'ports': results,
    }

    if not results.count():
        raise Http404()

    return render(request, 'host_detail.html', data)


@require_GET
@staff_required
def web_view(request, domain):
    pages = Website.objects.select_related().filter(
        domain=domain).order_by('url', '-timestamp').distinct('url').prefetch_related('app_set')

    data = {
        'domain': domain,
        'pages': pages,
    }

    if not pages.count():
        raise Http404()

    return render(request, 'web_detail.html', data)
