from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (TestimoniumAntiquariansForm,
                                 TestimoniumCommentaryForm, TestimoniumForm,
                                 TestimoniumLinkWorkForm)
from rard.research.models import Book, Testimonium, Work
from rard.research.models.base import TestimoniumLink
from rard.research.views.fragment import HistoricalBaseCreateView


class TestimoniumCreateView(PermissionRequiredMixin, HistoricalBaseCreateView):
    form_class = TestimoniumForm
    success_url_name = 'testimonium:detail'
    title = 'Create Testimonium'
    permission_required = ('research.add_testimonium',)


class TestimoniumListView(
        LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Testimonium
    permission_required = ('research.view_testimonium',)


class TestimoniumDetailView(
        LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Testimonium
    permission_required = ('research.view_testimonium',)


@method_decorator(require_POST, name='dispatch')
class TestimoniumDeleteView(
        LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Testimonium
    success_url = reverse_lazy('testimonium:list')
    permission_required = ('research.delete_testimonium',)


class TestimoniumUpdateView(
        LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Testimonium
    form_class = TestimoniumForm
    permission_required = ('research.change_testimonium',)

    def get_success_url(self, *args, **kwargs):
        return reverse('testimonium:detail', kwargs={'pk': self.object.pk})


class TestimoniumUpdateAntiquariansView(TestimoniumUpdateView):

    model = Testimonium
    form_class = TestimoniumAntiquariansForm
    permission_required = ('research.change_testimonium',)
    template_name = 'research/testimonium_antiquarians_form.html'


class TestimoniumUpdateCommentaryView(TestimoniumUpdateView):

    model = Testimonium
    form_class = TestimoniumCommentaryForm
    permission_required = ('research.change_testimonium',)
    # use a different template showing commentary field
    template_name = 'research/testimonium_commentary_form.html'


class TestimoniumAddWorkLinkView(
        LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'research/add_work_link.html'
    form_class = TestimoniumLinkWorkForm
    permission_required = (
        'research.change_testimonium',
        'research.add_testimoniumlink',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'testimonium:detail', kwargs={'pk': self.get_testimonium().pk}
        )

    def get_testimonium(self, *args, **kwargs):
        if not getattr(self, 'testimonium', False):
            self.testimonium = get_object_or_404(
                Testimonium,
                pk=self.kwargs.get('pk')
            )
        return self.testimonium

    def form_valid(self, form):
        data = form.cleaned_data
        work = data['work']
        book = data['book']
        link_to_antiquarians = work.antiquarian_set.all() or [None]

        for antiquarian in link_to_antiquarians:
            data['testimonium'] = self.get_testimonium()
            data['antiquarian'] = antiquarian
            data['book'] = book
            TestimoniumLink.objects.get_or_create(**data)

        return super().form_valid(form)

    def get_work(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.work = None

        if self.request.method == 'GET':
            work_pk = self.request.GET.get('work', None)
        elif self.request.method == 'POST':
            work_pk = self.request.POST.get('work', None)

        if work_pk is not None:
            try:
                self.work = Work.objects.get(pk=work_pk)
            except Work.DoesNotExist:
                raise Http404
        return self.work

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'testimonium': self.get_testimonium(),
            'work': self.get_work(),
        })
        return context

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values['work'] = self.get_work()
        return values


class TestimoniumRemoveLinkView(
        LoginRequiredMixin, PermissionRequiredMixin, RedirectView):

    # base class for both remove work and remove book from a testimonium
    permission_required = ('research.edit_testimonium',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'testimonium:detail', kwargs={'pk': self.testimonium.pk}
        )

    def get_linked_object(self, *args, **kwargs):
        if not getattr(self, 'linked', False):
            self.linked = get_object_or_404(
                self.linked_class,
                pk=self.kwargs.get('linked_pk')
            )
        return self.linked

    def get_testimonium(self, *args, **kwargs):
        if not getattr(self, 'testimonium', False):
            self.testimonium = get_object_or_404(
                Testimonium,
                pk=self.kwargs.get('pk')
            )
        return self.testimonium

    def post(self, request, *args, **kwargs):
        testimonium = self.get_testimonium()
        data = {
            'testimonium': testimonium,
            self.link_object_field_name: self.get_linked_object()
        }
        qs = TestimoniumLink.objects.filter(**data)
        qs.delete()
        return redirect(self.get_success_url())


@method_decorator(require_POST, name='dispatch')
class TestimoniumRemoveWorkLinkView(TestimoniumRemoveLinkView):

    linked_class = Work
    link_object_field_name = 'work'


@method_decorator(require_POST, name='dispatch')
class TestimoniumRemoveBookLinkView(TestimoniumRemoveLinkView):

    linked_class = Book
    link_object_field_name = 'book'
