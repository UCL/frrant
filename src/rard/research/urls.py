from django.conf.urls import include
from django.urls import path

import rard.research.views as views

# common urls for both fragments and testimonia for shared views that we
# want to expose under different namespaces
common_patterns = [
    path("original-text/<pk>/update/", views.OriginalTextUpdateView.as_view(), name="update_original_text"),
    path("original-text/<pk>/delete/", views.OriginalTextDeleteView.as_view(), name="delete_original_text"),
    path("original-text/<pk>/create-translation/", views.TranslationCreateView.as_view(), name="create_translation"),
    path("translation/<pk>/update/", views.TranslationUpdateView.as_view(), name="update_translation"),
    path("translation/<pk>/delete/", views.TranslationDeleteView.as_view(), name="delete_translation"),
]

# app_name = "research"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("comment/<pk>/delete/", views.CommentDeleteView.as_view(), name="delete_comment"),
    path("text-field/<pk>/comments/", views.TextObjectFieldCommentListView.as_view(), name="list_comments_on_text"),
    path('antiquarian/', include(([
        path('list/', views.AntiquarianListView.as_view(), name='list'),
        path("create/", views.AntiquarianCreateView.as_view(), name="create"),
        path("<pk>/", views.AntiquarianDetailView.as_view(), name="detail"),
        path("<pk>/update/", views.AntiquarianUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.AntiquarianDeleteView.as_view(), name="delete"),
        path("<pk>/work/create/", views.AntiquarianWorkCreateView.as_view(), name="create_work"),
        path("<pk>/works/", views.AntiquarianWorksUpdateView.as_view(), name="update_works"),
    ], 'research'), namespace='antiquarian')),
    path('work/', include(([
        path('list/', views.WorkListView.as_view(), name='list'),
        path("create/", views.WorkCreateView.as_view(), name="create_anonymous"),
        path("<pk>/", views.WorkDetailView.as_view(), name="detail"),
        path("<pk>/update/", views.WorkUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.WorkDeleteView.as_view(), name="delete"),
        path("<pk>/create-book/", views.BookCreateView.as_view(), name="create_book"),
        path("book/<pk>/update/", views.BookUpdateView.as_view(), name="update_book"),
        path("book/<pk>/delete/", views.BookDeleteView.as_view(), name="delete_book"),
    ], 'research'), namespace='work')),
    path('fragment/', include(([
        path('list/', views.FragmentListView.as_view(), name='list'),
        path("create/", views.FragmentCreateView.as_view(), name="create"),
        path("<pk>/update/", views.FragmentUpdateView.as_view(), name="update"),
        path("<pk>/update/commentary/", views.FragmentUpdateCommentaryView.as_view(), name="update_commentary"),
        path("<pk>/update/antiquarians/", views.FragmentUpdateAntiquariansView.as_view(), name="update_antiquarians"),
        path("<pk>/link-work/", views.FragmentAddWorkLinkView.as_view(), name="add_work_link"),
        path("<pk>/unlink-work/<linked_pk>", views.FragmentRemoveWorkLinkView.as_view(), name="remove_work_link"),
        path("<pk>/unlink-book/<linked_pk>", views.FragmentRemoveBookLinkView.as_view(), name="remove_book_link"),
        path("<pk>/delete/", views.FragmentDeleteView.as_view(), name="delete"),
        path("<pk>/", views.FragmentDetailView.as_view(), name="detail"),
        path("<pk>/create-original-text/", views.FragmentOriginalTextCreateView.as_view(), name="create_original_text"),
        # include common urls here
        path("", include(common_patterns)),
    ], 'research'), namespace='fragment')),
    path('testimonium/', include(([
        path('list/', views.TestimoniumListView.as_view(), name='list'),
        path("create/", views.TestimoniumCreateView.as_view(), name="create"),
        path("<pk>/update/", views.TestimoniumUpdateView.as_view(), name="update"),
        path("<pk>/update/commentary/", views.TestimoniumUpdateCommentaryView.as_view(), name="update_commentary"),
        path("<pk>/update/antiquarians/", views.TestimoniumUpdateAntiquariansView.as_view(), name="update_antiquarians"),
        path("<pk>/link-work/", views.TestimoniumAddWorkLinkView.as_view(), name="add_work_link"),
        path("<pk>/unlink-work/<linked_pk>", views.TestimoniumRemoveWorkLinkView.as_view(), name="remove_work_link"),
        path("<pk>/unlink-book/<linked_pk>", views.TestimoniumRemoveBookLinkView.as_view(), name="remove_book_link"),
        path("<pk>/delete/", views.TestimoniumDeleteView.as_view(), name="delete"),
        path("<pk>/", views.TestimoniumDetailView.as_view(), name="detail"),
        path("<pk>/create-original-text/", views.TestimoniumOriginalTextCreateView.as_view(), name="create_original_text"),
        path("", include(common_patterns)),
        # include common urls here
    ], 'research'), namespace='testimonium')),
    path('topic/', include(([
        path('list/', views.TopicListView.as_view(), name='list'),
        path("create/", views.TopicCreateView.as_view(), name="create"),
        path("<slug>/", views.TopicDetailView.as_view(), name="detail"),
        path("<slug>/update/", views.TopicUpdateView.as_view(), name="update"),
        path("<slug>/delete/", views.TopicDeleteView.as_view(), name="delete"),
    ], 'research'), namespace='topic')),
    path('concordance/', include(([
        path('list/', views.ConcordanceListView.as_view(), name='list'),
        path("original-text/<pk>/create/", views.ConcordanceCreateView.as_view(), name="create"),
        path("<pk>/update/", views.ConcordanceUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.ConcordanceDeleteView.as_view(), name="delete"),
    ], 'research'), namespace='concordance')),
    path('search/', include(([
        path('', views.SearchView.as_view(), name='home'),
    ], 'research'), namespace='search')),

]
