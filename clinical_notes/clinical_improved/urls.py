from django.conf.urls import url

from . import views

# TODO: Add url patterns for looking up patients fields and values. 
urlpatterns = [
    url(r'^$', views.index, name='index'),
#    url(r'^load/$', views.load),
    url(r'^execute/$', views.execute, name='execute'),
    url(r'^view/$', views.view, name='view'),
    url(r'^fields/([0-9]+)/$', views.fields, name='fields'),
    url(r'^values/([0-9]+)/([0-9]+)/([0-9]+)/$', views.values, name='values'),
]
