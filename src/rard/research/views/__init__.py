from .antiquarian import (
    AntiquarianBibliographyCreateView,
    AntiquarianConcordanceCreateView,
    AntiquarianConcordanceDeleteView,
    AntiquarianConcordanceUpdateView,
    AntiquarianCreateView,
    AntiquarianDeleteView,
    AntiquarianDetailView,
    AntiquarianListView,
    AntiquarianUpdateIntroductionView,
    AntiquarianUpdateView,
    AntiquarianWorkCreateView,
    AntiquarianWorksUpdateView,
    MoveLinkView,
)
from .apparatus_criticus import (
    ApparatusCriticusSearchView,
    CreateApparatusCriticusLineView,
    DeleteApparatusCriticusLineView,
    RefreshOriginalTextContentView,
    UpdateApparatusCriticusLineView,
)
from .bibliography import (
    BibliographyDeleteView,
    BibliographyListView,
    BibliographyUpdateView,
)
from .citing_work import (
    CitingAuthorCreateView,
    CitingAuthorCreateWorkView,
    CitingAuthorDeleteView,
    CitingAuthorDetailView,
    CitingAuthorFullListView,
    CitingAuthorListView,
    CitingAuthorUpdateView,
    CitingWorkCreateView,
    CitingWorkDeleteView,
    CitingWorkDetailView,
    CitingWorkUpdateView,
)
from .comments import CommentDeleteView, TextObjectFieldCommentListView
from .concordance import (
    ConcordanceCreateView,
    ConcordanceDeleteView,
    ConcordanceListView,
    ConcordanceUpdateView,
)
from .fragment import (
    AddAppositumFragmentLinkView,
    AddAppositumGeneralLinkView,
    AnonymousFragmentConvertToFragmentView,
    AnonymousFragmentCreateView,
    AnonymousFragmentDeleteView,
    AnonymousFragmentDetailView,
    AnonymousFragmentListView,
    AnonymousFragmentUpdateCommentaryView,
    AnonymousFragmentUpdateView,
    AppositumCreateView,
    FragmentAddWorkLinkView,
    FragmentCreateView,
    FragmentDeleteView,
    FragmentDetailView,
    FragmentListView,
    FragmentUpdateAntiquariansView,
    FragmentUpdateCommentaryView,
    FragmentUpdateView,
    FragmentUpdateWorkLinkView,
    MoveAnonymousTopicLinkView,
    RemoveAppositumLinkView,
    RemoveFragmentLinkView,
    UnlinkedFragmentConvertToAnonymousView,
    UnlinkedFragmentListView,
)
from .history import HistoryListView
from .home import HomeView
from .mention import MentionSearchView
from .original_text import (
    AnonymousFragmentOriginalTextCreateView,
    FragmentOriginalTextCreateView,
    OriginalTextDeleteView,
    OriginalTextUpdateAuthorView,
    OriginalTextUpdateView,
    TestimoniumOriginalTextCreateView,
)
from .search import SearchView
from .testimonium import (
    RemoveTestimoniumLinkView,
    TestimoniumAddWorkLinkView,
    TestimoniumCreateView,
    TestimoniumDeleteView,
    TestimoniumDetailView,
    TestimoniumListView,
    TestimoniumUpdateAntiquariansView,
    TestimoniumUpdateCommentaryView,
    TestimoniumUpdateView,
    TestimoniumUpdateWorkLinkView,
)
from .topic import (
    MoveTopicView,
    TopicCreateView,
    TopicDeleteView,
    TopicDetailView,
    TopicListView,
    TopicUpdateView,
)
from .translation import (
    TranslationCreateView,
    TranslationDeleteView,
    TranslationUpdateView,
)
from .work import (
    BookCreateView,
    BookDeleteView,
    BookUpdateIntroductionView,
    BookUpdateView,
    WorkCreateView,
    WorkDeleteView,
    WorkDetailView,
    WorkListView,
    WorkUpdateIntroductionView,
    WorkUpdateView,
)

__all__ = [
    "AddAppositumFragmentLinkView",
    "AddAppositumGeneralLinkView",
    "AntiquarianBibliographyCreateView",
    "AntiquarianConcordanceCreateView",
    "AntiquarianConcordanceDeleteView",
    "AntiquarianConcordanceUpdateView",
    "AntiquarianCreateView",
    "AntiquarianWorkCreateView",
    "AntiquarianDeleteView",
    "AntiquarianDetailView",
    "AntiquarianListView",
    "MoveLinkView",
    "AntiquarianUpdateView",
    "AntiquarianUpdateIntroductionView",
    "AntiquarianWorksUpdateView",
    "ApparatusCriticusSearchView",
    "BibliographyDeleteView",
    "BibliographyListView",
    "BibliographyUpdateView",
    "BookCreateView",
    "BookUpdateView",
    "BookUpdateIntroductionView",
    "BookDeleteView",
    "CitingAuthorCreateView",
    "CitingAuthorCreateWorkView",
    "CitingAuthorDeleteView",
    "CitingAuthorDetailView",
    "CitingAuthorListView",
    "CitingAuthorFullListView",
    "CitingAuthorUpdateView",
    "CitingWorkCreateView",
    "CitingWorkDeleteView",
    "CitingWorkDetailView",
    "CitingWorkUpdateView",
    "CommentDeleteView",
    "ConcordanceCreateView",
    "ConcordanceDeleteView",
    "ConcordanceListView",
    "ConcordanceUpdateView",
    "CreateApparatusCriticusLineView",
    "DeleteApparatusCriticusLineView",
    "RefreshOriginalTextContentView",
    "UpdateApparatusCriticusLineView",
    "AnonymousFragmentCreateView",
    "AnonymousFragmentDeleteView",
    "AnonymousFragmentConvertToFragmentView",
    "AnonymousFragmentDetailView",
    "AnonymousFragmentListView",
    "AnonymousFragmentOriginalTextCreateView",
    "AnonymousFragmentUpdateCommentaryView",
    "AnonymousFragmentUpdateView",
    "AppositumCreateView",
    "FragmentAddWorkLinkView",
    "RemoveFragmentLinkView",
    "FragmentUpdateCommentaryView",
    "FragmentCreateView",
    "FragmentDeleteView",
    "UnlinkedFragmentConvertToAnonymousView",
    "FragmentDetailView",
    "FragmentListView",
    "FragmentOriginalTextCreateView",
    "FragmentUpdateView",
    "FragmentUpdateWorkLinkView",
    "FragmentUpdateAntiquariansView",
    "HistoryListView",
    "HomeView",
    "MentionSearchView",
    "MoveTopicView",
    "MoveAnonymousTopicLinkView",
    "OriginalTextDeleteView",
    "OriginalTextUpdateAuthorView",
    "OriginalTextUpdateView",
    "RemoveAppositumLinkView",
    "SearchView",
    "RemoveTestimoniumLinkView",
    "TestimoniumAddWorkLinkView",
    "TestimoniumCreateView",
    "TestimoniumDeleteView",
    "TestimoniumDetailView",
    "TestimoniumListView",
    "TestimoniumUpdateView",
    "TestimoniumUpdateWorkLinkView",
    "TestimoniumUpdateAntiquariansView",
    "TestimoniumUpdateCommentaryView",
    "TextObjectFieldCommentListView",
    "TestimoniumOriginalTextCreateView",
    "TopicCreateView",
    "TopicDeleteView",
    "TopicDetailView",
    "TopicListView",
    "TopicUpdateView",
    "TranslationCreateView",
    "TranslationUpdateView",
    "TranslationDeleteView",
    "UnlinkedFragmentListView",
    "WorkCreateView",
    "WorkDeleteView",
    "WorkDetailView",
    "WorkListView",
    "WorkUpdateView",
    "WorkUpdateIntroductionView",
]
