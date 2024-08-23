from django.conf.urls import include
from django.urls import path
from django_distill import distill_path

import rard.research.views as views
from rard.research.models import Antiquarian
from rard.research.models.citing_work import CitingAuthor, CitingWork
from rard.research.models.fragment import AnonymousFragment, Fragment
from rard.research.models.testimonium import Testimonium
from rard.research.models.topic import Topic
from rard.research.models.work import Work


def get_model_pks(model):
    for instance in model.objects.all():
        yield {"pk": instance.pk}


def get_topic_slugs():
    for topic in Topic.objects.all():
        yield {"slug": topic.slug}


urlpatterns = [
    distill_path("index.html", views.HomeView.as_view(), name="home"),
    path(
        "antiquarian/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.AntiquarianListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.AntiquarianDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(Antiquarian),
                    ),
                    distill_path(
                        "<pk>/bibliography/index.html",
                        views.BibliographySectionView.as_view(),
                        name="bibliography",
                        distill_func=lambda: get_model_pks(Antiquarian),
                    ),
                ],
                "research",
            ),
            namespace="antiquarian",
        ),
    ),
    path(
        "bibliography/",
        include(
            (
                [
                    distill_path(
                        "index.html",
                        views.BibliographyOverviewView.as_view(),
                        name="overview",
                    ),
                    distill_path(
                        "list/index.html",
                        views.BibliographyListView.as_view(),
                        name="list",
                    ),
                    # distill_path(
                    #     "<pk>/index.html",
                    #     views.BibliographyDetailView.as_view(),
                    #     name="detail",
                    #     distill_func=lambda: get_model_pks(BibliographyItem),
                    # ),
                ],
                "research",
            ),
            namespace="bibliography",
        ),
    ),
    path(
        "work/",
        include(
            (
                [
                    distill_path(
                        "list/index.html", views.WorkListView.as_view(), name="list"
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.WorkDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(Work),
                    ),
                ],
                "research",
            ),
            namespace="work",
        ),
    ),
    path(
        "fragment/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.FragmentListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.FragmentDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(Fragment),
                    ),
                ],
                "research",
            ),
            namespace="fragment",
        ),
    ),
    path(
        "anonymous/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.AnonymousFragmentListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.AnonymousFragmentDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(AnonymousFragment),
                    ),
                ],
                "research",
            ),
            namespace="anonymous_fragment",
        ),
    ),
    path(
        "testimonium/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.TestimoniumListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.TestimoniumDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(Testimonium),
                    ),
                ],
                "research",
            ),
            namespace="testimonium",
        ),
    ),
    path(
        "topic/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.TopicListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "<slug>/index.html",
                        views.TopicDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_topic_slugs(),
                    ),
                ],
                "research",
            ),
            namespace="topic",
        ),
    ),
    path(
        "concordance/",
        include(
            (
                [  # TODO after new structure
                    distill_path(
                        "list/", views.ConcordanceListView.as_view(), name="list"
                    ),
                ],
                "research",
            ),
            namespace="concordance",
        ),
    ),
    path(
        "search/",
        include(
            (
                [
                    distill_path("index.html", views.SearchView.as_view(), name="home"),
                ],
                "research",
            ),
            namespace="search",
        ),
    ),
    path(
        "unlinked/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.UnlinkedFragmentListView.as_view(),
                        name="list",
                    ),
                ],
                "research",
            ),
            namespace="unlinked_fragment",
        ),
    ),
    path(
        "",
        include(
            (
                [
                    distill_path(
                        "<model_name>/<pk>/history/index.html",
                        views.HistoryListView.as_view(),
                        name="list",
                    ),
                ],
                "research",
            ),
            namespace="history",
        ),
    ),
    path(
        "citing-author/",
        include(
            (
                [
                    distill_path(
                        "list/index.html",
                        views.CitingAuthorListView.as_view(),
                        name="list",
                    ),
                    distill_path(
                        "all/index.html",
                        views.CitingAuthorFullListView.as_view(),
                        name="all",
                    ),
                    distill_path(
                        "<pk>/index.html",
                        views.CitingAuthorDetailView.as_view(),
                        name="detail",
                        distill_func=lambda: get_model_pks(CitingAuthor),
                    ),
                    distill_path(
                        "work/<pk>/index.html",
                        views.CitingWorkDetailView.as_view(),
                        name="work_detail",
                        distill_func=lambda: get_model_pks(CitingWork),
                    ),
                ],
                "research",
            ),
            namespace="citingauthor",
        ),
    ),
]
