# coding=utf-8

import re

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.datetime_safe import datetime
from django.utils.http import is_safe_url, urlencode
from django.views.decorators.http import require_http_methods, require_POST, require_GET

from ujscert.headquarter.utils import staff_required
from ujscert.vul.forms import AnonymousReportForm, ReportForm, ImageUploadForm, LoginForm, ProfileForm, ReviewForm, \
    CommentForm
from ujscert.vul.models import Vul, MemberVul, WhiteHat, AnonymousVul, Invitation, \
    STATUS_CHOICES, STATUS_UNVERIFIED, STATUS_CONFIRMED, STATUS_FIXED, STATUS_IGNORED, \
    STATUS_TO_REVIEW, Comment, Timeline, TIMELINE_CHANGE_STATUS
from ujscert.vul.utils import send_rendered_mail, get_client_ip


@transaction.atomic()
@require_http_methods(['GET', 'POST'])
def submit_view(request):
    the_form = ReportForm if request.user.is_authenticated() \
        else AnonymousReportForm

    # anonymous
    if request.method == 'POST':
        form = the_form(request.POST, request.FILES)

        if form.is_valid():
            entry = form.save(commit=False)

            dest = None
            if request.user.is_authenticated():
                entry.author = WhiteHat.objects.get(user=request.user)
                author = 'member'
                anonymous = False
            else:
                entry.ip = get_client_ip(request)
                dest = redirect('track', track_id=entry.uuid.hex)
                author = 'anonymous'
                anonymous = True

            entry.save()
            entry.vul_ptr.anonymous = anonymous
            entry.vul_ptr.save()

            redirect_args = {
                'vid': entry.pk,
                'author': author,
            }

            # 发送邮件至管理员
            try:
                for user in User.objects.filter(is_staff=True, email__isnull=False):
                    send_rendered_mail(user.email, 'submission_alert', {
                        'review_url': request.build_absolute_uri(reverse('detail', kwargs=redirect_args))
                    })
            except:
                pass

            if not dest:
                dest = redirect('detail', **redirect_args)

            return dest

        return render(request, 'submit.html', {'form': form})

    else:
        form = the_form(initial={'detail': render_to_string('report_template.txt')})
        return render(request, 'submit.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated() and request.user.is_active:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next')
    safe_next_url = next_url if is_safe_url(next_url) else reverse('home')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)

        if form.is_valid():
            login(request, form.get_user())
            return redirect(safe_next_url)

        response = redirect('login')
        response['Location'] += ('?' + urlencode({'next': safe_next_url, 'err': ''}))
        return response

    form = LoginForm()
    data = {'form': form, 'err': 'err' in request.GET, 'next': safe_next_url}
    return render(request, 'login.html', data)


@require_GET
def track_view(request, track_id):
    vul = get_object_or_404(Vul, uuid=track_id)
    return render(request, 'track.html', {'vul': vul})


@require_POST
def upload_img(request):
    form = ImageUploadForm(request.POST, request.FILES)
    if form.is_valid():
        result = form.save()
        return JsonResponse({'status': 'successful', 'url': result.img.url})

    response = JsonResponse({'error': form.errors})
    response.status_code = 400
    return response


@require_GET
def logout_view(request):
    logout(request)
    return redirect('home')


@require_GET
@login_required
def profile_view(request, uid='self'):
    if (request.user.is_staff or request.user.is_superuser) and uid != 'self':
        condition = {'pk': uid}
    else:
        condition = {'user': request.user}

    profile = get_object_or_404(WhiteHat, **condition)

    # in case of javascript: or other malicious url
    if not re.match(r'^https?://', profile.site):
        profile.site = 'http://' + profile.site

    vuls = MemberVul.objects.filter(author=profile)[:10]
    return render(request, 'profile.html', dict(vuls=vuls, profile=profile))


@require_http_methods(['GET', 'POST'])
@login_required
def update_profile_view(request):
    profile = get_object_or_404(WhiteHat, user=request.user)
    if request.method == 'GET':
        edit_form = ProfileForm(instance=profile)

    else:
        edit_form = ProfileForm(request.POST, instance=profile)
        if edit_form.is_valid():
            edit_form.save()
            return redirect('profile')

    return render_to_response(
        'edit_profile.html',
        {'form': edit_form},
        context_instance=RequestContext(request))


@require_POST
@transaction.atomic()
@login_required
def add_comment_view(request, vid):
    if not request.is_ajax():
        return HttpResponseBadRequest()

    form = CommentForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(form.errors.as_json())

    whitehat = WhiteHat.objects.get(user=request.user)
    if not (request.user.is_staff and request.user.is_superuser):
        vul = get_object_or_404(MemberVul, author=whitehat, pk=vid)
    else:
        vul = get_object_or_404(Vul, pk=vid)

    comment = Comment(content=form.data.get('content'), vul=vul, author=whitehat)
    comment.save()
    return JsonResponse({'status': 'ok'})


@require_http_methods(['GET', 'POST'])
@transaction.atomic()
@login_required
def detail_view(request, author, vid):
    is_anonymous = author == 'anonymous'
    model = AnonymousVul if is_anonymous else MemberVul

    if request.user.is_staff or request.user.is_superuser:
        vul = get_object_or_404(model, pk=vid)
        status_before = vul.status

        if request.method == 'GET':
            form = ReviewForm(instance=vul)
        else:
            form = ReviewForm(request.POST, instance=vul)

            if not form.is_valid():
                return HttpResponseBadRequest()

            status_current = form.cleaned_data['status']
            form.save()

            if is_anonymous and vul.email and status_before == STATUS_UNVERIFIED:
                if status_current == STATUS_IGNORED:
                    send_rendered_mail(vul.email, 'ignored', {'vul': vul})
                elif status_current == STATUS_CONFIRMED:
                    invitation, created = Invitation.objects.get_or_create(email=vul.email)
                    invite_url = request.build_absolute_uri(reverse('invite', kwargs={'code': invitation.code.hex}))
                    send_rendered_mail(vul.email, 'invite', {'invite_url': invite_url})
                elif status_current == STATUS_TO_REVIEW:
                    vul.status = status_current = STATUS_FIXED

            # status has been changed
            if status_current != status_before:
                timeline = Timeline(event_type=TIMELINE_CHANGE_STATUS, vul=vul)
                timeline.extra = {'status': vul.status}
                timeline.save()

                if status_current in (STATUS_CONFIRMED, STATUS_IGNORED):
                    vul.confirmed = datetime.now()

                elif status_current == STATUS_FIXED:
                    vul.fixed = datetime.now()

            vul.save()

            response = redirect('detail', author=author, vid=vid)
            response['Location'] += '?success'
            return response

    else:
        # only show vul report by user itself
        whitehat = WhiteHat.objects.get(user=request.user)
        vul = get_object_or_404(MemberVul, author=whitehat, pk=vid)
        form = None

    events = Timeline.objects.filter(vul=vul).order_by('timestamp')
    comments = Comment.objects.filter(vul=vul).order_by('timestamp')
    comment_form = CommentForm()
    template_name = 'detail_print.html' if 'print' in request.GET else 'detail.html'

    return render(request, template_name, {
        'vul': vul,
        'form': form,
        'comment_form': comment_form,
        'events': events,
        'comments': comments,
        'is_anonymous': is_anonymous,
        'status_choices': STATUS_CHOICES,
    })


@require_GET
@staff_required
def review_list_view(request, author, status=0):
    page = request.GET.get('page')

    author_choices = (('all', '全部'), ('member', '注册用户'), ('anonymous', '匿名用户'))
    status_choices = (('all', '全部'),) + STATUS_CHOICES

    model_map = {'all': Vul, 'member': MemberVul, 'anonymous': AnonymousVul}

    if author not in model_map:
        return HttpResponseBadRequest()

    model = model_map[author]

    if status != 'all':
        status = int(status)
        reviews = model.objects.filter(status=status)
    else:
        reviews = model.objects.all()

    paginator = Paginator(reviews, 20)

    try:
        vuls = paginator.page(page)
    except PageNotAnInteger:
        vuls = paginator.page(1)
    except EmptyPage:
        vuls = paginator.page(paginator.num_pages)

    data = {
        'author': author,
        'items': vuls,
        'status': status,
        'status_choices': status_choices,
        'author_choices': author_choices,
    }

    return render(request, 'review_list.html', data)


@transaction.atomic()
@require_http_methods(['GET', 'POST'])
def register_view(request, code):
    if request.user.is_authenticated():
        return redirect('profile')

    invitation = get_object_or_404(Invitation, code=code, valid=True)

    if request.method == 'GET':
        form = UserCreationForm()
    else:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # create user
            user = form.save(commit=False)
            user.email = invitation.email
            form.save()

            # deactivate invitation
            invitation.valid = False
            invitation.save()

            # move vul under user
            for vul in AnonymousVul.objects.filter(email=user.email):
                vul.vul_ptr.anonymous = False
                vul.vul_ptr.save()

                new_vul = MemberVul(vul_ptr=vul.vul_ptr)
                new_vul.__dict__.update(vul.__dict__)
                new_vul.author = user
                new_vul.save()
                vul.delete(keep_parents=True)

            return redirect('register_successful')

    return render(request, 'register.html', {'invite': invitation, 'form': form})


@require_GET
def rank_view(request):
    top10 = WhiteHat.objects.filter(public=True).order_by('-reputation')[:10]
    return render(request, 'rank.html', {'top10': top10})
