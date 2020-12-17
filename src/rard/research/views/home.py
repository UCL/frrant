from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.views.generic import ListView, TemplateView

from rard.research.models import Fragment


class HomeView(TemplateView):
    def get_template_names(self):
        if not self.request.user.is_authenticated:
            return ['pages/front.html']
        else:
            return ['research/home.html']


class AnonymousListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ('research.view_fragment',)
    template_name = 'research/anonymous_list.html'

    def get_queryset(self):
        from django.db.models import F
        return super().get_queryset().filter(is_anonymous=True).annotate(
            topic=F('topics__name')
        ).order_by('topic', 'topiclink__order')
