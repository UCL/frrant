from django.conf.urls import include
from django.urls import path

import rard.research.views as views

# app_name = "research"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path('antiquarian/', include(([
        path('list/', views.AntiquarianListView.as_view(), name='list'),
        path("create/", views.AntiquarianCreateView.as_view(), name="create"),
        path("<pk>/", views.AntiquarianDetailView.as_view(), name="detail"),
        path("<pk>/update/", views.AntiquarianUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.AntiquarianDeleteView.as_view(), name="delete"),
        path("<pk>/work/create/", views.AntiquarianWorkCreateView.as_view(), name="create_work"),
        path("<pk>/works/", views.AntiquarianWorksUpdateView.as_view(), name="update_works"),
        # path("<pk>/work/<work_pk>/remove/", views.AntiquarianRemoveWorkView.as_view(), name="remove_work"),
    ], 'research'), namespace='antiquarian')),
    path('work/', include(([
        path('list/', views.WorkListView.as_view(), name='list'),
        # path("<antiquarian_pk>/create/", views.WorkCreateView.as_view(), name="create"),
        path("create/", views.WorkCreateView.as_view(), name="create_anonymous"),
        path("<pk>/", views.WorkDetailView.as_view(), name="detail"),
        path("<pk>/update/", views.WorkUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.WorkDeleteView.as_view(), name="delete"),
    ], 'research'), namespace='work')),
    path('fragment/', include(([
        path('list/', views.FragmentListView.as_view(), name='list'),
        path("create/", views.FragmentCreateView.as_view(), name="create"),
        path("<pk>/update/", views.FragmentUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.FragmentDeleteView.as_view(), name="delete"),
        path("<pk>/", views.FragmentDetailView.as_view(), name="detail"),
        # common urls between fragment and testimonium
        path("<pk>/create-original-text/", views.FragmentOriginalTextCreateView.as_view(), name="create_original_text"),
        path("original-text/<pk>/update/", views.OriginalTextUpdateView.as_view(), name="update_original_text"),
        path("original-text/<pk>/delete/", views.OriginalTextDeleteView.as_view(), name="delete_original_text"),
        path("original-text/<pk>/create-translation/", views.TranslationCreateView.as_view(), name="create_translation"),
        path("translation/<pk>/update/", views.TranslationUpdateView.as_view(), name="update_translation"),
        path("translation/<pk>/delete/", views.TranslationDeleteView.as_view(), name="delete_translation"),
        # for comments on a text object belonging to a fragment
        path("text-field/<pk>/comments/", views.TextObjectFieldCommentListView.as_view(), name="list_comments_on_text"),
        path("comment/<pk>/delete/", views.CommentDeleteView.as_view(), name="delete_comment"),

    ], 'research'), namespace='fragment')),
    path('topic/', include(([
        path('list/', views.TopicListView.as_view(), name='list'),
        path("create/", views.TopicCreateView.as_view(), name="create"),
        path("<slug>/", views.TopicDetailView.as_view(), name="detail"),
        path("<slug>/update/", views.TopicUpdateView.as_view(), name="update"),
        path("<slug>/delete/", views.TopicDeleteView.as_view(), name="delete"),
    ], 'research'), namespace='topic')),

]
