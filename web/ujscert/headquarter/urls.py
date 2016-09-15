from ujscert.headquarter import views
from django.conf.urls import url

urlpatterns = [
    url(r'^api/ping$', views.pong_api_view, name='ping'),
    url(r'^api/index/host$', views.index_host_api_view, name="index_banner"),
    url(r'^api/index/web$', views.index_web_api_view, name="index_web"),
    url(r'^api/index/feed$', views.feed_api_view),
    url(r'^api/apps$', views.apps_api_view),

    url(r'^property/search$', views.search_home_view, name="search_home"),
    url(r'^property/search/$', views.search_view, name="search"),
    url(r'^property/host/(?P<ip>(\d{1,3}\.){3}\d{1,3})$', views.host_view, name="host_detail"),
    url(r'^property/web/(?P<domain>\S+)$', views.web_view, name="web_detail"),
    url(r'^property/export/$', views.export_view, name="export"),
    url(r'^alerts$', views.alert_view, name="alerts"),
]
