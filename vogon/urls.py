"""vogon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework_nested import routers as nrouters
from annotations.views import *
from annotations import views


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'appellation', views.AppellationViewSet)
router.register(r'predicate', views.PredicateViewSet)
router.register(r'relation', views.RelationViewSet)
router.register(r'text', views.TextViewSet)
router.register(r'repository', views.RepositoryViewSet)
router.register(r'temporalbounds', views.TemporalBoundsViewSet)
router.register(r'user', views.UserViewSet)
router.register(r'concept', views.ConceptViewSet)
router.register(r'type', views.TypeViewSet)
router.register(r'textcollection', views.TextCollectionViewSet)

repository_router = nrouters.NestedSimpleRouter(router, r'repository', lookup='repository')
repository_router.register('collection', views.RemoteCollectionViewSet, base_name='repository')

remotecollection_router = nrouters.NestedSimpleRouter(repository_router, r'collection', lookup='collection')
remotecollection_router.register('resource', views.RemoteResourceViewSet, base_name='collection')

urlpatterns = [
    url(r'^accounts/profile/$', views.dashboard, name='dashboard'),
    url(r'^accounts/settings/$', views.user_settings),
    url(r'^accounts/register/$', views.register),
    url(r'^accounts/register/success/$', views.home),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rest/', include(router.urls)),
    url(r'^rest/', include(repository_router.urls)),
    url(r'^rest/', include(remotecollection_router.urls)),
    url(r'^network/$', views.network, name="network"),
    url(r'^text/$', views.list_texts, name="list_texts"),
    url(r'^text/(?P<textid>[0-9]+)/$', views.text, name="text"),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^$', views.home)
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
