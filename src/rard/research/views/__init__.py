from .antiquarian import (AntiquarianBibliographyCreateView,
                          AntiquarianConcordanceCreateView,
                          AntiquarianConcordanceDeleteView,
                          AntiquarianConcordanceUpdateView,
                          AntiquarianCreateView, AntiquarianDeleteView,
                          AntiquarianDetailView, AntiquarianListView,
                          AntiquarianUpdateIntroductionView,
                          AntiquarianUpdateView, AntiquarianWorkCreateView,
                          AntiquarianWorksUpdateView, MoveLinkView)
from .bibliography import (BibliographyDeleteView, BibliographyListView,
                           BibliographyUpdateView)
from .citing_work import (CitingAuthorListView, CitingWorkDeleteView,
                          CitingWorkDetailView, CitingWorkUpdateView)
from .comments import CommentDeleteView, TextObjectFieldCommentListView
from .concordance import (ConcordanceCreateView, ConcordanceDeleteView,
                          ConcordanceListView, ConcordanceUpdateView)
from .fragment import (AddAppositumFragmentLinkView,
                       AddAppositumGeneralLinkView,
                       AnonymousFragmentCreateView,
                       AnonymousFragmentDeleteView,
                       AnonymousFragmentDetailView, AnonymousFragmentListView,
                       AnonymousFragmentUpdateCommentaryView,
                       AnonymousFragmentUpdateView, AppositumCreateView,
                       FragmentAddWorkLinkView, FragmentCreateView,
                       FragmentDeleteView, FragmentDetailView,
                       FragmentListView, FragmentRemoveBookLinkView,
                       FragmentRemoveWorkLinkView,
                       FragmentUpdateAntiquariansView,
                       FragmentUpdateCommentaryView, FragmentUpdateView,
                       RemoveAppositumLinkView)
from .history import HistoryListView
from .home import HomeView
from .mention import MentionSearchView
from .original_text import (AnonymousFragmentOriginalTextCreateView,
                            FragmentOriginalTextCreateView,
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
from .topic import (MoveTopicView, TopicCreateView, TopicDeleteView,
                    TopicDetailView, TopicListView, TopicUpdateView)
from .translation import (TranslationCreateView, TranslationDeleteView,
                          TranslationUpdateView)
from .work import (BookCreateView, BookDeleteView, BookUpdateView,
                   WorkCreateView, WorkDeleteView, WorkDetailView,
                   WorkListView, WorkUpdateView)

__all__ = [
    'AddAppositumFragmentLinkView',
    'AddAppositumGeneralLinkView',
    'AntiquarianBibliographyCreateView',
    'AntiquarianConcordanceCreateView',
    'AntiquarianConcordanceDeleteView',
    'AntiquarianConcordanceUpdateView',
    'AntiquarianCreateView',
    'AntiquarianWorkCreateView',
    'AntiquarianDeleteView',
    'AntiquarianDetailView',
    'AntiquarianListView',
    'MoveLinkView',
    'AntiquarianUpdateView',
    'AntiquarianUpdateIntroductionView',
    'AntiquarianWorksUpdateView',
    'BibliographyDeleteView',
    'BibliographyListView',
    'BibliographyUpdateView',
    'BookCreateView',
    'BookUpdateView',
    'BookDeleteView',
    'CitingAuthorListView',
    'CitingWorkDeleteView',
    'CitingWorkDetailView',
    'CitingWorkUpdateView',
    'CommentDeleteView',
    'ConcordanceCreateView',
    'ConcordanceDeleteView',
    'ConcordanceListView',
    'ConcordanceUpdateView',
    'AnonymousFragmentCreateView',
    'AnonymousFragmentDeleteView',
    'AnonymousFragmentDetailView',
    'AnonymousFragmentListView',
    'AnonymousFragmentOriginalTextCreateView',
    'AnonymousFragmentUpdateCommentaryView',
    'AnonymousFragmentUpdateView',
    'AppositumCreateView',
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
    'HistoryListView',
    'HomeView',
    'MentionSearchView',
    'MoveTopicView',
    'OriginalTextDeleteView',
    'OriginalTextUpdateView',
    'RemoveAppositumLinkView',
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
