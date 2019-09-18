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
from django.urls import include, path, re_path
from django.contrib import admin
# from django.urls import path
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
router.register(r'dateappellation', views.rest_views.DateAppellationViewSet)






#Error Handlers
handler403 = 'annotations.exceptions.custom_403_handler'

urlpatterns = [
    re_path(r'^$', views.main_views.home, name='home'),
    re_path(r'^about/$', views.main_views.about, name='about'),

    re_path(r'^users/$', views.user_views.list_user, name='users'),
    re_path(r'^activity/$', views.main_views.recent_activity),

    re_path(r'^users/(?P<userid>[0-9]+)/$', views.user_views.user_details, name="user_details"),
    re_path(r'^accounts/login/$', views.user_views.login_view, name='login_fallback'),
    re_path(r'^accounts/logout/$', views.user_views.logout_view, name='logout'),
    re_path(r'^accounts/profile/', views.user_views.dashboard, name='dashboard'),
    re_path(r'^accounts/projects/', views.user_views.user_projects, name='user_projects'),
    re_path(r'^accounts/settings/$', views.user_views.user_settings, name='settings'),
    # re_path(r'^accounts/register/$', views.user_views.register, name='register'),
    # re_path('', include('social.apps.django_app.re_paths', namespace='social')),
    # re_path(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name="logout"),
    # re_path(r'^accounts/', include('django.contrib.auth.urls')),

    re_path('', include('allauth.urls')),

    path('admin/', admin.site.urls),

    re_path(r'^rest/', include(router.urls)),

    # url(r'^text/$', views.search_views.TextSearchView.as_view(), name='text_search'),
    # url(r'^text/$', views.text_views.texts, name='text_search'),

    # TODO: network views need to be refactored for performance on v. large
    #  datasets. Even moderately sized queries are crashing.
    # url(r'^network/$', views.network_views.network, name="network"),
    # url(r'^network/data/$', views.network_views.network_data, name="network-data"),
    re_path(r'^network/text/(?P<text_id>[0-9]+)/$', views.network_views.network_for_text, name="network_for_text"),

    re_path(r'^relationtemplate/add/$', views.relationtemplate_views.add_relationtemplate, name="add_relationtemplate"),
    re_path(r'^relationtemplate/(?P<template_id>[0-9]+)/$', views.relationtemplate_views.get_relationtemplate, name="get_relationtemplate"),
    re_path(r'^relationtemplate/(?P<template_id>[0-9]+)/create/$', views.relationtemplate_views.create_from_relationtemplate, name="create_from_relationtemplate"),
    re_path(r'^relationtemplate[/]?$', views.relationtemplate_views.list_relationtemplate, name='list_relationtemplate'),
    re_path(r'^relationtemplate/(?P<template_id>[0-9]+)/delete/$', views.relationtemplate_views.delete_relationtemplate, name='delete_relationtemplate'),

    # url(r'^text/add/upload/$', views.text_views.upload_file, name="file_upload"),
    # url(r'^text/(?P<textid>[0-9]+)/$', views.text_views.text, name="text"),
    re_path(r'^annotate/(?P<text_id>[0-9]+)/$', views.annotation_views.annotate, name="annotate"),
    re_path(r'^display/(?P<text_id>[0-9]+)/$', views.annotation_views.annotation_display, name="annotation-display"),

    re_path(r'^project/(?P<project_id>[0-9]+)/$', views.project_views.view_project, name='view_project'),
    re_path(r'^project/(?P<project_id>[0-9]+)/edit/$', views.project_views.edit_project, name='edit_project'),
    re_path(r'^project/create/$', views.project_views.create_project, name='create_project'),
    re_path(r'^project/$', views.project_views.list_projects, name='list_projects'),

    re_path(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    #re_path(r'^autocomplete/', include('autocomplete_light.urls')),    # TODO: are we still using this?

    re_path(r'^sign_s3$', views.aws_views.sign_s3, name="sign_s3"),

    # url(r'^concept/(?P<conceptid>[0-9]+)/$', views.data_views.concept_details, name='concept_details'),
    re_path(r'^relations/(?P<source_concept_id>[0-9]+)/(?P<target_concept_id>[0-9]+)/$', views.data_views.relation_details, name="relation_details"),
    re_path(r'^relations/$', views.annotation_views.relations, name="relations"),
    re_path(r'^relations/graph/$', views.annotation_views.relations_graph, name="relations_graph"),

    re_path(r'^concept/types$', conceptViews.list_concept_types),
    re_path(r'^concept/type/(?P<type_id>[0-9]+)/$', conceptViews.type, name="type"),
    re_path(r'^concept/$', conceptViews.concepts, name="concepts"),
    re_path(r'^concept/(?P<concept_id>[0-9]+)/$', conceptViews.concept, name='concept'),
    re_path(r'^concept/(?P<concept_id>[0-9]+)/add/$', conceptViews.add_concept, name='add_concept'),
    re_path(r'^concept/(?P<concept_id>[0-9]+)/edit/$', conceptViews.edit_concept, name='edit_concept'),
    re_path(r'^concept/(?P<concept_id>[0-9]+)/approve/$', conceptViews.approve_concept, name="approve_concept"),
    re_path(r'^concept/(?P<source_concept_id>[0-9]+)/merge/$', conceptViews.merge_concepts, name='merge_concepts'),

    # url(r'^concept_autocomplete/', views.search_views.concept_autocomplete, name='concept_autocomplete'),

    re_path(r'^quadruples/appellation/(?P<appellation_id>[0-9]+).xml$', views.quadruple_views.appellation_xml, name='appellation_xml'),
    re_path(r'^quadruples/relation/(?P<relation_id>[0-9]+).xml$', views.quadruple_views.relation_xml, name='relation_xml'),
    re_path(r'^quadruples/relationset/(?P<relationset_id>[0-9]+).xml$', views.quadruple_views.relationset_xml, name='relationset_xml'),
    re_path(r'^quadruples/text/(?P<text_id>[0-9]+)/(?P<user_id>[0-9]+).xml$', views.quadruple_views.text_xml, name='text_xml'),

    re_path(r'^repository/(?P<repository_id>[0-9]+)/collections/$', views.repository_views.repository_collections, name='repository_collections'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/browse/$', views.repository_views.repository_browse, name='repository_browse'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/search/$', views.repository_views.repository_search, name='repository_search'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/collections/(?P<collection_id>[0-9]+)/$', views.repository_views.repository_collection, name='repository_collection'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/text/(?P<text_id>[0-9]+)/$', views.repository_views.repository_text, name='repository_text'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/text/(?P<text_id>[0-9]+)/content/(?P<content_id>[0-9]+)/$', views.repository_views.repository_text_content, name='repository_text_content'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/$', views.repository_views.repository_details, name='repository_details'),
    re_path(r'^repository/(?P<repository_id>[0-9]+)/text/(?P<text_id>[0-9]+)/project/(?P<project_id>[0-9]+)$', views.repository_views.repository_text_add_to_project, name='repository_text_add_to_project'),

    re_path(r'^repository/$', views.repository_views.repository_list, name='repository_list'),

    re_path(r'^text/(?P<text_id>[0-9]+)/public/$', views.text_views.text_public, name='text_public'),

    #re_path(r'^annotate/image/(?P<text_id>[0-9]+)/$', views.annotation_views.annotate_image, name='annotate_image'),


    re_path(r'^sandbox/(?P<text_id>[0-9]+)/$', conceptViews.sandbox, name='sandbox'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
