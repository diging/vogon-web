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
from django.conf.urls import include, url, handler403
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework_nested import routers as nrouters
from annotations import views
from concepts import views as conceptViews


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'appellation', views.rest_views.AppellationViewSet)
router.register(r'predicate', views.rest_views.PredicateViewSet)
router.register(r'relation', views.rest_views.RelationViewSet)
router.register(r'relationset', views.rest_views.RelationSetViewSet)
router.register(r'text', views.rest_views.TextViewSet)
router.register(r'repository', views.rest_views.RepositoryViewSet)
router.register(r'temporalbounds', views.rest_views.TemporalBoundsViewSet)
router.register(r'user', views.rest_views.UserViewSet)
router.register(r'concept', views.rest_views.ConceptViewSet)
router.register(r'type', views.rest_views.TypeViewSet)
router.register(r'textcollection', views.rest_views.TextCollectionViewSet)

# TODO: do we still need this nested router business?
repository_router = nrouters.NestedSimpleRouter(router, r'repository', lookup='repository')
repository_router.register('collection', views.rest_views.RemoteCollectionViewSet, base_name='repository')

remotecollection_router = nrouters.NestedSimpleRouter(repository_router, r'collection', lookup='collection')
remotecollection_router.register('resource', views.rest_views.RemoteResourceViewSet, base_name='collection')


#Error Handlers
handler403 = 'annotations.exceptions.custom_403_handler'

urlpatterns = [
    url(r'^$', views.main_views.home, name='home'),
    url(r'^about/$', views.main_views.about, name='about'),

    url(r'^users/$', views.user_views.list_user, name='users'),
    url(r'^activity/$', views.main_views.recent_activity),

    url(r'^users/(?P<userid>[0-9]+)/$', views.user_views.user_details, name="user_details"),
    url(r'^accounts/profile/', views.user_views.dashboard, name='dashboard'),
    url(r'^accounts/projects/', views.user_views.user_projects, name='user_projects'),
    url(r'^accounts/settings/$', views.user_views.user_settings, name='settings'),
    # url(r'^accounts/register/$', views.user_views.register, name='register'),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
                          {'next_page': '/'}),
    url(r'^accounts/', include('django.contrib.auth.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^rest/', include(router.urls)),
    url(r'^rest/', include(repository_router.urls)),
    url(r'^rest/', include(remotecollection_router.urls)),

    # url(r'^text/$', views.search_views.TextSearchView.as_view(), name='text_search'),
    url(r'^text/$', views.main_views.home, name='text_search'),

    url(r'^network/$', views.network_views.network, name="network"),
    url(r'^network/data/$', views.network_views.network_data, name="network-data"),
    url(r'^network/text/(?P<text_id>[0-9]+)/$', views.network_views.network_for_text, name="network_for_text"),

    url(r'^relationtemplate/add/$', views.relationtemplate_views.add_relationtemplate, name="add_relationtemplate"),
    url(r'^relationtemplate/(?P<template_id>[0-9]+)/$', views.relationtemplate_views.get_relationtemplate, name="get_relationtemplate"),
    url(r'^relationtemplate/(?P<template_id>[0-9]+)/create/$', views.relationtemplate_views.create_from_relationtemplate, name="create_from_relationtemplate"),
    url(r'^relationtemplate[/]?$', views.relationtemplate_views.list_relationtemplate, name='list_relationtemplate'),

    url(r'^text/add/upload/$', views.text_views.upload_file, name="file_upload"),
    url(r'^text/(?P<textid>[0-9]+)/$', views.text_views.text, name="text"),

    url(r'^project/(?P<project_id>[0-9]+)/$', views.project_views.view_project, name='view_project'),
    url(r'^project/(?P<project_id>[0-9]+)/edit/$', views.project_views.edit_project, name='edit_project'),
    url(r'^project/create/$', views.project_views.create_project, name='create_project'),
    url(r'^project/$', views.project_views.list_projects, name='list_projects'),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^autocomplete/', include('autocomplete_light.urls')),    # TODO: are we still using this?

    url(r'^sign_s3$', views.aws_views.sign_s3, name="sign_s3"),

    url(r'^concept/(?P<conceptid>[0-9]+)/$', views.data_views.concept_details, name='concept_details'),
    url(r'^relations/(?P<source_concept_id>[0-9]+)/(?P<target_concept_id>[0-9]+)/$', views.data_views.relation_details, name="relation_details"),

    url(r'^concept/types$', conceptViews.list_concept_types),
    url(r'^concept/type/(?P<type_id>[0-9]+)/$', conceptViews.type, name="type"),

    url(r'^concept_autocomplete/', views.search_views.concept_autocomplete, name='concept_autocomplete'),

    url(r'^quadruples/appellation/(?P<appellation_id>[0-9]+).xml$', views.quadruple_views.appellation_xml, name='appellation_xml'),
    url(r'^quadruples/relation/(?P<relation_id>[0-9]+).xml$', views.quadruple_views.relation_xml, name='relation_xml'),
    url(r'^quadruples/relationset/(?P<relationset_id>[0-9]+).xml$', views.quadruple_views.relationset_xml, name='relationset_xml'),
    url(r'^quadruples/text/(?P<text_id>[0-9]+)/(?P<user_id>[0-9]+).xml$', views.quadruple_views.text_xml, name='text_xml'),

    url(r'^repository/(?P<repository_id>[0-9]+)/collections/$', views.repository_views.repository_collections, name='repository_collections'),
    url(r'^repository/(?P<repository_id>[0-9]+)/browse/$', views.repository_views.repository_browse, name='repository_browse'),
    url(r'^repository/(?P<repository_id>[0-9]+)/search/$', views.repository_views.repository_search, name='repository_search'),
    url(r'^repository/(?P<repository_id>[0-9]+)/collections/(?P<collection_id>[0-9]+)/$', views.repository_views.repository_collection, name='repository_collection'),
    url(r'^repository/(?P<repository_id>[0-9]+)/text/(?P<text_id>[0-9]+)/$', views.repository_views.repository_text, name='repository_text'),
    url(r'^repository/(?P<repository_id>[0-9]+)/text/(?P<text_id>[0-9]+)/content/(?P<content_id>[0-9]+)/$', views.repository_views.repository_text_content, name='repository_text_content'),
    url(r'^repository/(?P<repository_id>[0-9]+)/$', views.repository_views.repository_details, name='repository_details'),
    url(r'^repository/$', views.repository_views.repository_list, name='repository_list'),

    url(r'^annotate/image/(?P<text_id>[0-9]+)/$', views.annotation_views.annotate_image, name='annotate_image'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
