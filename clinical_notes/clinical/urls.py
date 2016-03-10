from django.conf.urls import url

from . import views

urlpatterns = [
	url(r'^$', views.index, name='index'),
	# url(r'^fields(?P<patient_id>[0-9]+)/$', views.fields), TODO: Get named parameters working....
	url(r'^fields/([0-9]+)/$', views.fields),
	url(r'^values/([0-9]+)/([0-9]+)/$', views.values),
	url(r'^notes/', views.home, name='home'),
]
