from .antiquarian import (AntiquarianBibliographyCreateView,
                          AntiquarianCreateView, AntiquarianDeleteView,
                          AntiquarianDetailView, AntiquarianListView,
                          AntiquarianUpdateView, AntiquarianWorkCreateView,
                          AntiquarianWorksUpdateView)
from .bibliography import (BibliographyDeleteView, BibliographyListView,
                           BibliographyUpdateView)
from .comments import CommentDeleteView, TextObjectFieldCommentListView
from .concordance import (ConcordanceCreateView, ConcordanceDeleteView,
                          ConcordanceListView, ConcordanceUpdateView)
from .fragment import (FragmentAddWorkLinkView, FragmentCreateView,
                       FragmentDeleteView, FragmentDetailView,
                       FragmentListView, FragmentRemoveBookLinkView,
                       FragmentRemoveWorkLinkView,
                       FragmentUpdateAntiquariansView,
                       FragmentUpdateCommentaryView, FragmentUpdateView)
from .home import HomeView
from .original_text import (FragmentOriginalTextCreateView,
                            OriginalTextDeleteView, OriginalTextUpdateView,
                            TestimoniumOriginalTextCreateView)
from .search import SearchView
from .testimonium import (TestimoniumAddWorkLinkView, TestimoniumCreateView,
                          TestimoniumDeleteView, TestimoniumDetailView,
                          TestimoniumListView, TestimoniumRemoveBookLinkView,
                          TestimoniumRemoveWorkLinkView,
                          TestimoniumUpdateAntiquariansView,
                          TestimoniumUpdateCommentaryView,
                          TestimoniumUpdateView)
from .topic import (TopicCreateView, TopicDeleteView, TopicDetailView,
                    TopicListView, TopicUpdateView)
from .translation import (TranslationCreateView, TranslationDeleteView,
                          TranslationUpdateView)
from .work import (BookCreateView, BookDeleteView, BookUpdateView,
                   WorkCreateView, WorkDeleteView, WorkDetailView,
                   WorkListView, WorkUpdateView)

__all__ = [
    'AntiquarianBibliographyCreateView',
    'AntiquarianCreateView',
    'AntiquarianWorkCreateView',
    'AntiquarianDeleteView',
    'AntiquarianDetailView',
    'AntiquarianListView',
    'AntiquarianUpdateView',
    'AntiquarianWorksUpdateView',
    'BibliographyDeleteView',
    'BibliographyListView',
    'BibliographyUpdateView',
    'BookCreateView',
    'BookUpdateView',
    'BookDeleteView',
    'CommentDeleteView',
    'ConcordanceCreateView',
    'ConcordanceDeleteView',
    'ConcordanceListView',
    'ConcordanceUpdateView',
    'FragmentAddWorkLinkView',
    'FragmentUpdateCommentaryView',
    'FragmentCreateView',
    'FragmentDeleteView',
    'FragmentDetailView',
    'FragmentListView',
    'FragmentOriginalTextCreateView',
    'FragmentRemoveWorkLinkView',
    'FragmentRemoveBookLinkView',
    'FragmentUpdateView',
    'FragmentUpdateAntiquariansView',
    'HomeView',
    'OriginalTextDeleteView',
    'OriginalTextUpdateView',
    'SearchView',
    'TestimoniumAddWorkLinkView',
    'TestimoniumCreateView',
    'TestimoniumDeleteView',
    'TestimoniumDetailView',
    'TestimoniumListView',
    'TestimoniumRemoveWorkLinkView',
    'TestimoniumRemoveBookLinkView',
    'TestimoniumUpdateView',
    'TestimoniumUpdateAntiquariansView',
    'TestimoniumUpdateCommentaryView',
    'TextObjectFieldCommentListView',
    'TestimoniumOriginalTextCreateView',
    'TopicCreateView',
    'TopicDeleteView',
    'TopicDetailView',
    'TopicListView',
    'TopicUpdateView',
    'TranslationCreateView',
    'TranslationUpdateView',
    'TranslationDeleteView',
    'WorkCreateView',
    'WorkDeleteView',
    'WorkDetailView',
    'WorkListView',
    'WorkUpdateView',
]
