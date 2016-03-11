from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^values/([0-9]+)/([0-9]+)/([0-9]+)/$', views.values),
    url(r'^notes/', views.home, name='home'),
]
