from .antiquarian import (
    AntiquarianConcordanceCreateView,
    AntiquarianConcordanceDeleteView,
    AntiquarianConcordanceUpdateView,
    AntiquarianCreateView,
    AntiquarianDeleteView,
    AntiquarianDetailView,
    AntiquarianIntroductionView,
    AntiquarianListView,
    AntiquarianUpdateIntroductionView,
    AntiquarianUpdateView,
    AntiquarianWorkCreateView,
    AntiquarianWorksUpdateView,
    MoveLinkView,
    refresh_bibliography_from_mentions,
)
from .apparatus_criticus import (
    ApparatusCriticusSearchView,
    CreateApparatusCriticusLineView,
    DeleteApparatusCriticusLineView,
    RefreshOriginalTextContentView,
    UpdateApparatusCriticusLineView,
)
from .bibliography import (
    BibliographyCreateInlineView,
    BibliographyCreateView,
    BibliographyDeleteView,
    BibliographyDetailView,
    BibliographyListView,
    BibliographyOverviewView,
    BibliographySectionView,
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
    OldConcordanceDeleteView,
    fetch_parts,
    fetch_works,
)
from .fragment import (
    AddAppositumAnonymousLinkView,
    AddAppositumFragmentLinkView,
    AddAppositumGeneralLinkView,
    AnonymousFragmentCommentaryView,
    AnonymousFragmentConvertToFragmentView,
    AnonymousFragmentCreateView,
    AnonymousFragmentDeleteView,
    AnonymousFragmentDetailView,
    AnonymousFragmentListView,
    AnonymousFragmentPublicCommentaryView,
    AnonymousFragmentUpdateCommentaryView,
    AnonymousFragmentUpdatePublicCommentaryView,
    AnonymousFragmentUpdateView,
    AppositumCreateView,
    FragmentAddWorkLinkView,
    FragmentCommentaryView,
    FragmentCreateView,
    FragmentDeleteView,
    FragmentDetailView,
    FragmentListView,
    FragmentPublicCommentaryView,
    FragmentUpdateAntiquariansView,
    FragmentUpdateCommentaryView,
    FragmentUpdatePublicCommentaryView,
    FragmentUpdateView,
    FragmentUpdateWorkLinkView,
    MoveAnonymousTopicLinkView,
    RemoveAnonymousAppositumLinkView,
    RemoveAppositumFragmentLinkView,
    RemoveAppositumLinkView,
    RemoveFragmentLinkView,
    UnlinkedFragmentConvertToAnonymousView,
    UnlinkedFragmentListView,
    duplicate_fragment,
    fetch_fragments,
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
    TestimoniumCommentaryView,
    TestimoniumCreateView,
    TestimoniumDeleteView,
    TestimoniumDetailView,
    TestimoniumListView,
    TestimoniumPublicCommentaryView,
    TestimoniumUpdateAntiquariansView,
    TestimoniumUpdateCommentaryView,
    TestimoniumUpdatePublicCommentaryView,
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
    BookIntroductionView,
    BookUpdateIntroductionView,
    BookUpdateView,
    WorkCreateView,
    WorkDeleteView,
    WorkDetailView,
    WorkIntroductionView,
    WorkListView,
    WorkUpdateIntroductionView,
    WorkUpdateView,
    fetch_books,
)

__all__ = [
    "AddAppositumAnonymousLinkView",
    "AddAppositumFragmentLinkView",
    "AddAppositumGeneralLinkView",
    "AntiquarianConcordanceCreateView",
    "AntiquarianConcordanceDeleteView",
    "AntiquarianConcordanceUpdateView",
    "AntiquarianCreateView",
    "AntiquarianWorkCreateView",
    "AntiquarianDeleteView",
    "AntiquarianDetailView",
    "AntiquarianIntroductionView",
    "AntiquarianListView",
    "MoveLinkView",
    "AntiquarianUpdateView",
    "AntiquarianUpdateIntroductionView",
    "AntiquarianWorksUpdateView",
    "ApparatusCriticusSearchView",
    "BibliographyDeleteView",
    "BibliographyListView",
    "BibliographyDetailView",
    "BibliographyCreateView",
    "BibliographyCreateInlineView",
    "BibliographyOverviewView",
    "BibliographyUpdateView",
    "BibliographySectionView",
    "BookCreateView",
    "BookIntroductionView",
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
    "OldConcordanceDeleteView",
    "CreateApparatusCriticusLineView",
    "DeleteApparatusCriticusLineView",
    "RefreshOriginalTextContentView",
    "UpdateApparatusCriticusLineView",
    "AnonymousFragmentCreateView",
    "AnonymousFragmentDeleteView",
    "AnonymousFragmentCommentaryView",
    "AnonymousFragmentConvertToFragmentView",
    "AnonymousFragmentDetailView",
    "AnonymousFragmentListView",
    "AnonymousFragmentOriginalTextCreateView",
    "AnonymousFragmentUpdateCommentaryView",
    "AnonymousFragmentPublicCommentaryView",
    "AnonymousFragmentUpdatePublicCommentaryView",
    "AnonymousFragmentUpdateView",
    "AppositumCreateView",
    "FragmentAddWorkLinkView",
    "RemoveFragmentLinkView",
    "FragmentUpdateCommentaryView",
    "FragmentUpdatePublicCommentaryView",
    "FragmentPublicCommentaryView",
    "FragmentCommentaryView",
    "FragmentCreateView",
    "FragmentDeleteView",
    "UnlinkedFragmentConvertToAnonymousView",
    "FragmentDetailView",
    "FragmentListView",
    "FragmentOriginalTextCreateView",
    "FragmentUpdateView",
    "FragmentUpdateWorkLinkView",
    "FragmentUpdateAntiquariansView",
    "fetch_fragments",
    "duplicate_fragment",
    "HistoryListView",
    "HomeView",
    "MentionSearchView",
    "MoveTopicView",
    "MoveAnonymousTopicLinkView",
    "OriginalTextDeleteView",
    "OriginalTextUpdateAuthorView",
    "OriginalTextUpdateView",
    "RemoveAppositumLinkView",
    "RemoveAppositumFragmentLinkView",
    "RemoveAnonymousAppositumLinkView",
    "SearchView",
    "RemoveTestimoniumLinkView",
    "TestimoniumAddWorkLinkView",
    "TestimoniumCommentaryView",
    "TestimoniumCreateView",
    "TestimoniumDeleteView",
    "TestimoniumDetailView",
    "TestimoniumListView",
    "TestimoniumUpdateView",
    "TestimoniumUpdateWorkLinkView",
    "TestimoniumUpdateAntiquariansView",
    "TestimoniumUpdateCommentaryView",
    "TestimoniumUpdatePublicCommentaryView",
    "TestimoniumPublicCommentaryView",
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
    "refresh_bibliography_from_mentions",
    "WorkUpdateIntroductionView",
    "WorkIntroductionView",
    "fetch_books",
    "fetch_works",
    "fetch_parts",
]
