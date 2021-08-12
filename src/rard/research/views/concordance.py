from django.core import paginator
from django.core.paginator import Paginator
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.models import (AnonymousFragment, Concordance, Fragment,
                                  OriginalText, original_text)
from rard.research.models.base import FragmentLink
from rard.research.views.mixins import CheckLockMixin


def concordancelistview(request):
    """Create a complete list of concordances for display in a table. Each row requires:
    - a display name
    - url for the relevant fragment/anonymous fragment
    - a set of concordances
    """
    # Get every original text instance that has at least one associated concordance
    original_text_queryset = OriginalText.objects.filter(
            concordances__isnull=False
        ).distinct().prefetch_related('owner','concordances')
    concordances_table_data = []

    # Original texts should appear once for each work link
    for ot in original_text_queryset:
        concordances = ot.concordances.all()
        identifiers = ot.concordance_identifiers # Get list of names from work links
        owner_url = ot.owner.get_absolute_url()
        if len(identifiers) == 0: # Anonymous fragments can have concordances but no links
            concordances_table_data.append({
                'frrant': {'url':owner_url,'display_name':ot.owner.get_display_name()}, # Use the anonymous fragment's display name instead
                'concordances': concordances
            })
        else:
            for frrant in identifiers:
                concordances_table_data.append({
                    'frrant': {'url':owner_url,'display_name':frrant},
                    'concordances': concordances
                })
    items = [len(row['concordances']) for row in concordances_table_data]
    max_length = max(items) if items else 0
    paginator = Paginator(concordances_table_data,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context_data = {
        'column_range': range(0, max_length),
        'page_obj': page_obj
    }
    return render(request, 'research/concordance_list.html', context_data)


class ConcordanceCreateView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, CreateView):

    check_lock_object = 'top_level_object'

    # create a concordance for an original text
    model = Concordance
    permission_required = ('research.add_concordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_original_text().owner
        if (not isinstance(self.get_original_text().owner, Fragment) and
            not isinstance(self.get_original_text().owner, AnonymousFragment)):
            raise Http404

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()

    def form_valid(self, form):
        self.original_text = self.get_original_text()
        concordance = form.save(commit=False)
        concordance.original_text = self.original_text
        return super().form_valid(form)

    def get_original_text(self, *args, **kwargs):
        if not getattr(self, 'original_text', False):
            self.original_text = get_object_or_404(
                OriginalText,
                pk=self.kwargs.get('pk')
            )
        return self.original_text

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'original_text': self.get_original_text(),
        })
        return context


class ConcordanceUpdateView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, UpdateView):

    check_lock_object = 'top_level_object'

    model = Concordance
    permission_required = ('research.change_concordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'original_text': self.object.original_text,
        })
        return context

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
        # o.owner.get_absolute_url()
        # return reverse('original_text:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class ConcordanceDeleteView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, DeleteView):
    check_lock_object = 'top_level_object'

    model = Concordance
    permission_required = ('research.delete_concordance',)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.top_level_object = self.get_object().original_text.owner
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.original_text.owner.get_absolute_url()
