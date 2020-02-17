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

from rest_framework_nested import routers
from annotations import views
from concepts import views as conceptViews
from accounts import views as account_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'annotate', views.annotation_views.AnnotationViewSet, base_name="annotate")
router.register(r'appellation', views.rest_views.AppellationViewSet)
router.register(r'predicate', views.rest_views.PredicateViewSet)
router.register(r'relation', views.rest_views.RelationViewSet)
router.register(r'relationset', views.annotation_views.RelationSetViewSet)
router.register(r'relationtemplate', views.relationtemplate_views.RelationTemplateViewSet, base_name='relationtemplate')
router.register(r'text', views.rest_views.TextViewSet)
router.register(r'repository', views.repository_views.RepositoryViewSet)
router.register(r'temporalbounds', views.rest_views.TemporalBoundsViewSet)
router.register(r'user', views.rest_views.UserViewSet)
router.register(r'concept', conceptViews.ConceptViewSet)
router.register(r'type', conceptViews.ConceptTypeViewSet, base_name='type')
router.register(r'textcollection', views.rest_views.TextCollectionViewSet)
router.register(r'dateappellation', views.rest_views.DateAppellationViewSet)
router.register(r'project', views.project_views.ProjectViewSet, base_name='project')
router.register(r'users', views.user_views.UserViewSet, basename='users')

repository_router = routers.NestedSimpleRouter(router, r'repository', lookup='repository')
repository_router.register(r'collections', views.repository_views.RepositoryCollectionViewSet, base_name='repository-collections')
repository_router.register(r'texts', views.repository_views.RepositoryTextView, base_name='repository-texts')

repository_content_router = routers.NestedSimpleRouter(repository_router, r'texts', lookup='texts')
repository_content_router.register(r'content', views.repository_views.RepositoryTextContentViewSet, base_name='repository-text-content')


#Error Handlers
handler403 = 'annotations.exceptions.custom_403_handler'

urlpatterns = [
    # REST Views
    path('api/v2/token/',  account_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v2/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v2/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/v2/github-token/', account_views.github_token, name="github_token"),
    path('api/v2/forgot-password/', account_views.ForgotPasswordView.as_view(), name="forgot_password"),
    path('api/v2/reset-password/', account_views.ResetPasswordView.as_view(), name="reset_password"),
    re_path(r'^api/v2/', include((router.urls, "vogon_rest"))),
    re_path(r'^api/v2/', include((repository_router.urls, "vogon_rest_repo"))),
    re_path(r'^api/v2/', include((repository_content_router.urls, "vogon_rest_repo_content"))),

    path('admin/', admin.site.urls),

    # TODO: Figure out whether quadruple views are required anymore
    re_path(r'^quadruples/appellation/(?P<appellation_id>[0-9]+).xml$', views.quadruple_views.appellation_xml, name='appellation_xml'),
    re_path(r'^quadruples/relation/(?P<relation_id>[0-9]+).xml$', views.quadruple_views.relation_xml, name='relation_xml'),
    re_path(r'^quadruples/relationset/(?P<relationset_id>[0-9]+).xml$', views.quadruple_views.relationset_xml, name='relationset_xml'),
    re_path(r'^quadruples/text/(?P<text_id>[0-9]+)/(?P<user_id>[0-9]+).xml$', views.quadruple_views.text_xml, name='text_xml'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
