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

# history_patterns = [
#     path("<content_type>/<pk>/history/", views.HistoryView.as_view(), name="history"),
# ]

# app_name = "research"
urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("ajax/move-link/", views.MoveLinkView.as_view(), name="move_link"),
    path("ajax/move-topic/", views.MoveTopicView.as_view(), name="move_move"),
    path("ajax/create-apparatus-criticus-line/", views.CreateApparatusCriticusLineView.as_view(), name="create_apparatus_criticus_line"),
    path("ajax/delete-apparatus-criticus-line/", views.DeleteApparatusCriticusLineView.as_view(), name="delete_apparatus_criticus_line"),
    path("ajax/update-apparatus-criticus-line/", views.UpdateApparatusCriticusLineView.as_view(), name="update_apparatus_criticus_line"),
    path("ajax/refresh-original-text-content/", views.RefreshOriginalTextContentView.as_view(), name="refresh_original_text_content"),
    # path("comment/<pk>/delete/", views.CommentDeleteView.as_view(), name="delete_comment"),
    # path("text-field/<pk>/comments/", views.TextObjectFieldCommentListView.as_view(), name="list_comments_on_text"),
    path('antiquarian/', include(([
        path('list/', views.AntiquarianListView.as_view(), name='list'),
        path("create/", views.AntiquarianCreateView.as_view(), name="create"),
        path("<pk>/", views.AntiquarianDetailView.as_view(), name="detail"),
        path("<pk>/update/", views.AntiquarianUpdateView.as_view(), name="update"),
        path("<pk>/update/introduction/", views.AntiquarianUpdateIntroductionView.as_view(), name="update_introduction"),
        path("<pk>/delete/", views.AntiquarianDeleteView.as_view(), name="delete"),
        path("<pk>/work/create/", views.AntiquarianWorkCreateView.as_view(), name="create_work"),
        path("<pk>/works/", views.AntiquarianWorksUpdateView.as_view(), name="update_works"),
        path("<pk>/bibliograpny/create/", views.AntiquarianBibliographyCreateView.as_view(), name="create_bibliography"),
        path("<pk>/concordance/create/", views.AntiquarianConcordanceCreateView.as_view(), name="create_concordance"),
        path("concordance/<pk>/update/", views.AntiquarianConcordanceUpdateView.as_view(), name="update_concordance"),
        path("concordance/<pk>/delete/", views.AntiquarianConcordanceDeleteView.as_view(), name="delete_concordance"),
    ], 'research'), namespace='antiquarian')),
    path('bibliography/', include(([
        path('list/', views.BibliographyListView.as_view(), name='list'),
        path("<pk>/update/", views.BibliographyUpdateView.as_view(), name="update"),
        path("<pk>/delete/", views.BibliographyDeleteView.as_view(), name="delete"),
    ], 'research'), namespace='bibliography')),
    path('work/', include(([
        path('list/', views.WorkListView.as_view(), name='list'),
        path("create/", views.WorkCreateView.as_view(), name="create"),
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
        path("<pk>/link-work/", views.FragmentAddWorkLinkView.as_view(), name="add_work_link"),
        path("remove-link/<pk>", views.RemoveFragmentLinkView.as_view(), name="remove_fragment_link"),
        path("<pk>/delete/", views.FragmentDeleteView.as_view(), name="delete"),
        path("<pk>/", views.FragmentDetailView.as_view(), name="detail"),
        path("<pk>/create-original-text/", views.FragmentOriginalTextCreateView.as_view(), name="create_original_text"),
        # include common urls here
        path("", include(common_patterns)),
    ], 'research'), namespace='fragment')),
    path('anonymous/', include(([
        path('list/', views.AnonymousFragmentListView.as_view(), name='list'),
        path("create/", views.AnonymousFragmentCreateView.as_view(), name="create"),
        path("<slug>/<owner_pk>/create-appositum/", views.AppositumCreateView.as_view(), name="create_appositum_for"),
        path("<pk>/appositum-link/", views.AddAppositumGeneralLinkView.as_view(), name="link"),
        path("<pk>/appositum-fragment-link/", views.AddAppositumFragmentLinkView.as_view(), name="link_fragment"),
        path("<pk>/unlink-apposita/<link_pk>", views.RemoveAppositumLinkView.as_view(), name="unlink_apposita"),
        path("<pk>/update/", views.AnonymousFragmentUpdateView.as_view(), name="update"),
        path("<pk>/update/commentary/", views.AnonymousFragmentUpdateCommentaryView.as_view(), name="update_commentary"),
        path("<pk>/delete/", views.AnonymousFragmentDeleteView.as_view(), name="delete"),
        path("<pk>/", views.AnonymousFragmentDetailView.as_view(), name="detail"),
        path("<pk>/create-original-text/", views.AnonymousFragmentOriginalTextCreateView.as_view(), name="create_original_text"),
        # include common urls here
        path("", include(common_patterns)),
    ], 'research'), namespace='anonymous_fragment')),
    path('testimonium/', include(([
        path('list/', views.TestimoniumListView.as_view(), name='list'),
        path("create/", views.TestimoniumCreateView.as_view(), name="create"),
        path("<pk>/update/", views.TestimoniumUpdateView.as_view(), name="update"),
        path("<pk>/update/commentary/", views.TestimoniumUpdateCommentaryView.as_view(), name="update_commentary"),
        path("<pk>/link-work/", views.TestimoniumAddWorkLinkView.as_view(), name="add_work_link"),
        path("remove-link/<pk>", views.RemoveTestimoniumLinkView.as_view(), name="remove_testimonium_link"),
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
        path('ajax/mention/', views.MentionSearchView.as_view(), name='mention'),
        path('ajax/apparatus-criticus/', views.ApparatusCriticusSearchView.as_view(), name='apparatus_criticus'),
    ], 'research'), namespace='search')),
    path('', include(([
        path("<model_name>/<pk>/history/", views.HistoryListView.as_view(), name="list"),
    ], 'research'), namespace='history')),

    path('citing-author/', include(([
        path('list/', views.CitingAuthorListView.as_view(), name='list'),
        path("work/<pk>/", views.CitingWorkDetailView.as_view(), name="work_detail"),
        path("work/<pk>/update/", views.CitingWorkUpdateView.as_view(), name="update_work"),
        path("work/<pk>/delete/", views.CitingWorkDeleteView.as_view(), name="delete_work"),
    ], 'research'), namespace='citingauthor')),

]
