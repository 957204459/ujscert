"""ujscert URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import TemplateView

import ujscert.vul.views as views

urlpatterns = [
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^submit$', views.submit_view, name='submit'),
    url(r'^upload$', views.upload_img),
    url(r'^about$', TemplateView.as_view(template_name='about.html'), name='about'),
    url(r'^top10$', views.rank_view, name='rank'),
    url(r'^legal$', TemplateView.as_view(template_name='legal.html'), name='legal'),

    url(r'^accounts/profile$', views.profile_view, name='profile'),
    url(r'^accounts/profile/edit$', views.update_profile_view, name='edit_profile'),
    url(r'^accounts/login/$', views.login_view, name='login'),
    url(r'^accounts/logout/$', views.logout_view, name='logout'),

    url(r'^profile/(?P<uid>\d+)$', views.profile_view, name='user_profile'),
    url(r'^detail/(?P<author>anonymous|member|all)/(?P<vid>\d+)$', views.detail_view, name='detail'),
    url(r'^comment/add/(?P<vid>\d+)', views.add_comment_view, name='add_comment'),
    url(r'^track/(?P<track_id>[0-9a-f]+)$', views.track_view, name='track'),

    url(r'^shop$', views.rewards_list_view, name='shop'),
    url(r'^shop/item/(?P<rid>\d+)', views.reward_detail_view, name='reward_detail'),

    url(r'^review/(?P<author>anonymous|member|all)/(?P<status>\d+|all)$', views.review_list_view, name='review'),
    url(r'^register/(?P<code>[0-9a-f]+)$', views.register_view, name='invite'),
    url(r'^register/successful$', TemplateView.as_view(template_name='register_successful.html'),
        name='register_successful'),

    url(r'^hq/', include('ujscert.headquarter.urls')),
    url(r'^captcha/', include('captcha.urls')),

    # 为隐藏后台, 可在 deploy_settings.py 中修改后台地址
    url(r'^%s/' % getattr(settings, 'ADMIN_PATH', 'admin'), admin.site.urls),
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
