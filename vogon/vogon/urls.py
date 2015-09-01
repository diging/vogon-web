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

urlpatterns = [
    url(r'^accounts/profile/$', views.dashboard),
    url(r'^accounts/settings/$', views.user_settings),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^rest/', include(router.urls)),
    url(r'^network/$', views.network),
    url(r'^text/(?P<textid>[0-9]+)/$', views.text),
    url(r'^text/add/$', views.add_text),
    url(r'^sources/repository/(?P<id>[0-9]+)', views.source_repository),
    url(r'^sources/repository$', views.source_repositories),
    url(r'^sources/collection/(?P<id>[0-9]+)', views.source_collection),
    url(r'^sources/collection$', views.source_collections),
    url(r'^sources/resource/(?P<id>[0-9]+)', views.source_resource),
    url(r'^sources/resource$', views.source_resources),
    url(r'^sources/retrieve/(?P<uri>.+)', views.source_retrieve),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
