from .antiquarian import (AntiquarianCreateView, AntiquarianDeleteView,
                          AntiquarianDetailView, AntiquarianListView,
                          AntiquarianUpdateView, AntiquarianWorkCreateView,
                          AntiquarianWorksUpdateView)
from .comments import CommentDeleteView, TextObjectFieldCommentListView
from .fragment import (FragmentCreateView, FragmentDeleteView,
                       FragmentDetailView, FragmentListView,
                       FragmentUpdateView)
from .home import HomeView
from .original_text import (FragmentOriginalTextCreateView,
                            OriginalTextDeleteView, OriginalTextUpdateView,
                            TestimoniumOriginalTextCreateView)
from .testimonium import (TestimoniumCreateView, TestimoniumDeleteView,
                          TestimoniumDetailView, TestimoniumListView,
                          TestimoniumUpdateView)
from .topic import (TopicCreateView, TopicDeleteView, TopicDetailView,
                    TopicListView, TopicUpdateView)
from .translation import (TranslationCreateView, TranslationDeleteView,
                          TranslationUpdateView)
from .work import (WorkCreateView, WorkDeleteView, WorkDetailView,
                   WorkListView, WorkUpdateView)

__all__ = [
    'AntiquarianCreateView',
    'AntiquarianWorkCreateView',
    'AntiquarianDeleteView',
    'AntiquarianDetailView',
    'AntiquarianListView',
    'AntiquarianUpdateView',
    'AntiquarianWorksUpdateView',
    'CommentDeleteView',
    'FragmentCreateView',
    'FragmentDeleteView',
    'FragmentDetailView',
    'FragmentListView',
    'FragmentOriginalTextCreateView',
    'FragmentUpdateView',
    'HomeView',
    'OriginalTextDeleteView',
    'OriginalTextUpdateView',
    'TestimoniumCreateView',
    'TestimoniumDeleteView',
    'TestimoniumDetailView',
    'TestimoniumListView',
    'TestimoniumUpdateView',
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
