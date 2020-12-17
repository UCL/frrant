from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http.response import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (AnonymousFragmentCommentaryForm,
                                 AnonymousFragmentForm, CitingWorkForm,
                                 FragmentAntiquariansForm,
                                 FragmentCommentaryForm, FragmentForm,
                                 FragmentLinkWorkForm, OriginalTextForm)
from rard.research.models import AnonymousFragment, Book, Fragment, Work
from rard.research.models.base import FragmentLink
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class OriginalTextCitingWorkView(LoginRequiredMixin, TemplateView):

    def get_forms(self):
        forms = {
            'original_text': OriginalTextForm(data=self.request.POST or None),
            'new_citing_work': CitingWorkForm(data=self.request.POST or None)
        }
        return forms

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'forms': self.get_forms(),
            # 'title': self.title
        })
        return context

    def forms_valid(self, form):
        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):

        context = self.get_context_data()
        forms = context['forms']
        # has the user chosen to create a new citing work?
        create_citing_work = 'new_citing_work' in self.request.POST

        # set requirements for fields dynamically according to whether
        # the user has chosen to create a new citing work or not
        forms['new_citing_work'].set_required(create_citing_work)
        forms['original_text'].set_citing_work_required(not create_citing_work)

        # now check the forms using the form validation
        forms_valid = all(
            [x.is_bound and x.is_valid() for x in forms.values()]
        )

        if forms_valid:
            return self.forms_valid(forms)

        # else reset the changes we made to required fields
        # and invite the user to try again
        forms['new_citing_work'].set_required(False)
        forms['original_text'].set_citing_work_required(False)

        return self.render_to_response(context)


class HistoricalBaseCreateView(OriginalTextCitingWorkView):

    template_name = 'research/base_create_form.html'

    def get_forms(self):
        forms = super().get_forms()
        forms['object'] = self.form_class(data=self.request.POST or None)
        return forms

    def forms_valid(self, forms):

        # save the objects here
        object_form = forms['object']
        saved_object = object_form.save()

        original_text = forms['original_text'].save(commit=False)
        original_text.owner = saved_object

        create_citing_work = 'new_citing_work' in self.request.POST

        if create_citing_work:
            original_text.citing_work = forms['new_citing_work'].save()

        original_text.save()

        return redirect(
            reverse(self.success_url_name, kwargs={'pk': saved_object.pk})
        )


class FragmentCreateView(PermissionRequiredMixin, HistoricalBaseCreateView):
    form_class = FragmentForm
    success_url_name = 'fragment:detail'
    title = 'Create Fragment'
    permission_required = ('research.add_fragment',)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'title': self.title
        })
        return context


class AnonymousFragmentCreateView(FragmentCreateView):
    form_class = AnonymousFragmentForm
    success_url_name = 'anonymous_fragment:detail'
    title = 'Create Anonymous Fragment'
    # permission_required = ('research.add_fragment',)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'title': self.title
        })
        return context


class FragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ('research.view_fragment',)


class AnonymousFragmentListView(FragmentListView):
    paginate_by = 10
    model = AnonymousFragment
    permission_required = ('research.view_fragment',)

    def get_queryset(self):
        qs = super().get_queryset()
        from django.db.models import F
        filtered = qs.annotate(
            topic=F('topics__name')).order_by('topic', 'order')
        return filtered


class FragmentDetailView(
        CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Fragment
    permission_required = ('research.view_fragment',)


class AnonymousFragmentDetailView(
        FragmentDetailView):
    model = AnonymousFragment
    permission_required = ('research.view_fragment',)


@method_decorator(require_POST, name='dispatch')
class FragmentDeleteView(CheckLockMixin, LoginRequiredMixin,
                         PermissionRequiredMixin, DeleteView):
    model = Fragment
    success_url = reverse_lazy('fragment:list')
    permission_required = ('research.delete_fragment',)


@method_decorator(require_POST, name='dispatch')
class AnonymousFragmentDeleteView(FragmentDeleteView):
    model = AnonymousFragment
    success_url = reverse_lazy('anonymous_fragment:list')
    permission_required = ('research.delete_fragment',)


class FragmentUpdateView(CheckLockMixin, LoginRequiredMixin,
                         PermissionRequiredMixin, UpdateView):
    model = Fragment
    form_class = FragmentForm
    permission_required = ('research.change_fragment',)

    def get_success_url(self, *args, **kwargs):
        return reverse('fragment:detail', kwargs={'pk': self.object.pk})


class AnonymousFragmentUpdateView(FragmentUpdateView):
    model = AnonymousFragment
    form_class = AnonymousFragmentForm
    permission_required = ('research.change_fragment',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'anonymous_fragment:detail', kwargs={'pk': self.object.pk}
        )


class FragmentUpdateAntiquariansView(FragmentUpdateView):
    model = Fragment
    form_class = FragmentAntiquariansForm
    permission_required = ('research.change_fragment',)
    # use a different template showing fewer fields
    template_name = 'research/fragment_antiquarians_form.html'


class FragmentUpdateCommentaryView(FragmentUpdateView):
    model = Fragment
    form_class = FragmentCommentaryForm
    permission_required = ('research.change_fragment',)
    template_name = 'research/fragment_commentary_form.html'


class AnonymousFragmentUpdateCommentaryView(FragmentUpdateView):
    model = AnonymousFragment
    form_class = AnonymousFragmentCommentaryForm
    permission_required = ('research.change_fragment',)
    template_name = 'research/fragment_commentary_form.html'


class FragmentAddWorkLinkView(CheckLockMixin, LoginRequiredMixin,
                              PermissionRequiredMixin, FormView):

    check_lock_object = 'fragment'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = 'research/add_work_link.html'
    form_class = FragmentLinkWorkForm
    permission_required = (
        'research.change_fragment',
        'research.add_fragmentlink',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'fragment:detail', kwargs={'pk': self.get_fragment().pk}
        )

    def get_fragment(self, *args, **kwargs):
        if not getattr(self, 'fragment', False):
            self.fragment = get_object_or_404(
                Fragment,
                pk=self.kwargs.get('pk')
            )
        return self.fragment

    def form_valid(self, form):
        data = form.cleaned_data
        work = data['work']
        book = data['book']
        link_to_antiquarians = work.antiquarian_set.all() or [None]

        for antiquarian in link_to_antiquarians:
            data['fragment'] = self.get_fragment()
            data['antiquarian'] = antiquarian
            data['book'] = book
            self.form_class.objects.get_or_create(**data)

        return super().form_valid(form)

    def get_work(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.work = None
        if self.request.method == 'GET':
            work_pk = self.request.GET.get('work', None)
        elif self.request.method == 'POST':
            work_pk = self.request.POST.get('work', None)
        if work_pk:
            try:
                self.work = Work.objects.get(pk=work_pk)
            except Work.DoesNotExist:
                raise Http404
        return self.work

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'fragment': self.get_fragment(),
            'work': self.get_work(),
        })
        return context

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values['work'] = self.get_work()
        return values


class FragmentRemoveLinkView(CheckLockMixin, LoginRequiredMixin,
                             PermissionRequiredMixin, RedirectView):

    check_lock_object = 'fragment'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_fragment()
        return super().dispatch(request, *args, **kwargs)

    # base class for both remove work and remove book from a fragment
    permission_required = ('research.change_fragment',)

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'fragment:detail', kwargs={'pk': self.fragment.pk}
        )

    def get_linked_object(self, *args, **kwargs):
        if not getattr(self, 'linked', False):
            self.linked = get_object_or_404(
                self.linked_class,
                pk=self.kwargs.get('linked_pk')
            )
        return self.linked

    def get_fragment(self, *args, **kwargs):
        if not getattr(self, 'fragment', False):
            self.fragment = get_object_or_404(
                Fragment,
                pk=self.kwargs.get('pk')
            )
        return self.fragment

    def post(self, request, *args, **kwargs):
        fragment = self.get_fragment()
        data = {
            'fragment': fragment,
            self.link_object_field_name: self.get_linked_object()
        }
        qs = FragmentLink.objects.filter(**data)
        qs.delete()
        return redirect(self.get_success_url())


@method_decorator(require_POST, name='dispatch')
class FragmentRemoveWorkLinkView(FragmentRemoveLinkView):

    linked_class = Work
    link_object_field_name = 'work'


@method_decorator(require_POST, name='dispatch')
class FragmentRemoveBookLinkView(FragmentRemoveLinkView):

    linked_class = Book
    link_object_field_name = 'book'
