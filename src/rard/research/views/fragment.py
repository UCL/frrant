from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.exceptions import ObjectDoesNotExist
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
                                 AnonymousFragmentForm,
                                 AppositumFragmentLinkForm,
                                 AppositumGeneralLinkForm,
                                 FragmentAntiquariansForm,
                                 FragmentCommentaryForm, FragmentForm,
                                 FragmentLinkWorkForm, OriginalTextForm)
from rard.research.models import (AnonymousFragment, Antiquarian, Book,
                                  CitingAuthor, CitingWork, Fragment, Work)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class OriginalTextCitingWorkView(LoginRequiredMixin, TemplateView):

    def get_forms(self):
        forms = {
            'original_text': OriginalTextForm(
                citing_author=self.get_citing_author_from_form(),
                citing_work=self.get_citing_work_from_form(),
                data=self.request.POST or None
            ),
        }
        return forms

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'forms': self.get_forms(),
            'citing_author': self.get_citing_author_from_form(),
            'citing_work': self.get_citing_work_from_form(),
        })
        return context

    def forms_valid(self, form):
        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):

        context = self.get_context_data()
        forms = context['forms']

        if 'create_object' in self.request.POST:

            # now check the forms using the form validation
            forms_valid = all(
                [x.is_bound and x.is_valid() for x in forms.values()]
            )
            if forms_valid:
                return self.forms_valid(forms)

        else:
            for _, form in forms.items():
                form.errors.clear()

        return self.render_to_response(context)

    def get_citing_author_from_form(self, *args, **kwargs):
        # look for author in the GET or POST parameters
        self.citing_author = None
        if self.request.method == 'GET':
            author_pk = self.request.GET.get('citing_author', None)
        elif self.request.method == 'POST':
            author_pk = self.request.POST.get('citing_author', None)
        if author_pk:
            try:
                self.citing_author = CitingAuthor.objects.get(pk=author_pk)
            except CitingAuthor.DoesNotExist:
                raise Http404
        return self.citing_author

    def get_citing_work_from_form(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.citing_work = None
        if self.request.method == 'GET':
            author_pk = self.request.GET.get('citing_work', None)
        elif self.request.method == 'POST':
            author_pk = self.request.POST.get('citing_work', None)
        if author_pk:
            try:
                self.citing_work = CitingWork.objects.get(pk=author_pk)
            except CitingWork.DoesNotExist:
                raise Http404
        return self.citing_work


class HistoricalBaseCreateView(OriginalTextCitingWorkView):

    template_name = 'research/base_create_form.html'

    def get_forms(self):
        forms = super().get_forms()
        forms['object'] = self.form_class(data=self.request.POST or None)
        return forms

    def post_process_saved_object(self, saved_object):
        # override this to do extra things to the saved
        # object before redirect
        pass

    def forms_valid(self, forms):

        # save the objects here
        object_form = forms['object']
        self.saved_object = object_form.save()

        original_text = forms['original_text'].save(commit=False)
        original_text.owner = self.saved_object

        original_text.save()

        self.post_process_saved_object(self.saved_object)

        return redirect(
            self.get_success_url()
        )

    def get_success_url(self):
        return reverse(
            self.success_url_name, kwargs={'pk': self.saved_object.pk}
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
    permission_required = ('research.add_anonymousfragment',)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'title': self.title
        })
        return context


class AppositumCreateView(AnonymousFragmentCreateView):

    title = 'Create Appositum'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'title': self.title,
            'owner_for': self.get_owner_for()
        })
        return context

    def post_process_saved_object(self, saved_object):
        # we need to link our anon fragment to the
        # new owner
        new_owner = self.get_owner_for()
        if isinstance(new_owner, Fragment):
            new_owner.apposita.add(saved_object)
        elif isinstance(new_owner, Antiquarian):
            AppositumFragmentLink.objects.get_or_create(
                anonymous_fragment=saved_object,
                antiquarian=new_owner
            )
        elif isinstance(new_owner, Work):
            # loop through the owners of the work
            # and create links for each
            for antiquarian in new_owner.antiquarian_set.all():
                AppositumFragmentLink.objects.get_or_create(
                    anonymous_fragment=saved_object,
                    antiquarian=antiquarian,
                    work=new_owner
                )

    def get_owner_for(self):
        if getattr(self, 'owner_for', False):
            return self.owner_for

        what = self.kwargs.get('slug')
        owner_pk = self.kwargs.get('owner_pk')

        lookup = {
            'antiquarian': Antiquarian,
            'work': Work,
            'fragment': Fragment,
        }
        obj_class = lookup.get(what, None)

        if not obj_class:
            raise Http404
        try:
            self.owner_for = obj_class.objects.get(pk=owner_pk)
        except ObjectDoesNotExist:
            raise Http404

        return self.owner_for


class FragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ('research.view_fragment',)


class AnonymousFragmentListView(FragmentListView):
    paginate_by = 10
    model = AnonymousFragment
    permission_required = ('research.view_fragment',)

    def get_queryset(self):
        # do not show anon fragment that are appositum to other things
        qs = super().get_queryset().filter(
            appositumfragmentlinks_from__isnull=True
        )
        from django.db.models import F
        filtered = qs.annotate(
            topic=F('topics__name'),
            topic_order=F('topics__order')
        ).order_by('topic_order', 'order')
        return filtered


class AddAppositumGeneralLinkView(CheckLockMixin, LoginRequiredMixin,
                                  PermissionRequiredMixin, FormView):

    check_lock_object = 'anonymous_fragment'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = 'research/add_appositum_link.html'
    form_class = AppositumGeneralLinkForm
    permission_required = (
        'research.change_anonymousfragment',
        'research.add_appositumfragmentlink',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'anonymous_fragment:detail',
            kwargs={'pk': self.get_anonymous_fragment().pk}
        )

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, 'anonymous_fragment', False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment,
                pk=self.kwargs.get('pk')
            )
        return self.anonymous_fragment

    def form_valid(self, form):
        data = form.cleaned_data
        work = data['work']
        book = data['book']
        exclusive = data['exclusive']

        antiquarian = data['antiquarian']
        # though they browsed to the work via the antiquarian,
        # if there are multiple authors of that work we need to
        # link them all
        link_to_antiquarians = \
            work.antiquarian_set.all() \
            if work and not exclusive \
            else [antiquarian]

        for antiquarian in link_to_antiquarians:
            data['anonymous_fragment'] = self.get_anonymous_fragment()
            data['antiquarian'] = antiquarian
            data['work'] = work
            data['book'] = book
            AppositumFragmentLink.objects.get_or_create(**data)

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

    def get_antiquarian(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.antiquarian = None
        if self.request.method == 'GET':
            antiquarian_pk = self.request.GET.get('antiquarian', None)
        elif self.request.method == 'POST':
            antiquarian_pk = self.request.POST.get('antiquarian', None)
        if antiquarian_pk:
            try:
                self.antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
            except Antiquarian.DoesNotExist:
                raise Http404
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'anonymous_fragment': self.get_anonymous_fragment(),
            'antiquarian': self.get_antiquarian(),
            'work': self.get_work(),
        })
        return context

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values['antiquarian'] = self.get_antiquarian()
        values['work'] = self.get_work()
        return values


class AddAppositumFragmentLinkView(CheckLockMixin, LoginRequiredMixin,
                                   PermissionRequiredMixin, FormView):

    check_lock_object = 'anonymous_fragment'

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = 'research/add_appositum_fragment_link.html'

    form_class = AppositumFragmentLinkForm
    permission_required = (
        'research.change_anonymousfragment',
        'research.add_appositumfragmentlink',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'anonymous_fragment:detail',
            kwargs={'pk': self.get_anonymous_fragment().pk}
        )

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, 'anonymous_fragment', False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment,
                pk=self.kwargs.get('pk')
            )
        return self.anonymous_fragment

    def form_valid(self, form):
        data = form.cleaned_data
        fragment = data['linked_to']
        if fragment:
            fragment.apposita.add(self.anonymous_fragment)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'anonymous_fragment': self.get_anonymous_fragment(),
        })
        return context


@method_decorator(require_POST, name='dispatch')
class RemoveAppositumLinkView(CheckLockMixin, LoginRequiredMixin,
                              PermissionRequiredMixin, RedirectView):

    check_lock_object = 'anonymous_fragment'
    permission_required = ('research.change_anonymousfragment',)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, 'anonymous_fragment', False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment,
                pk=self.kwargs.get('pk')
            )
        return self.anonymous_fragment

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'anonymous_fragment:detail',
            kwargs={'pk': self.anonymous_fragment.pk}
        )

    def get_appositum_link(self, *args, **kwargs):
        if not getattr(self, 'link', False):
            self.link = get_object_or_404(
                AppositumFragmentLink,
                pk=self.kwargs.get('link_pk')
            )
        return self.link

    def post(self, request, *args, **kwargs):
        anonymous_fragment = self.get_anonymous_fragment()
        link = self.get_appositum_link()
        if not link.linked_to:
            link.delete()
        else:
            # if linked to a fragment remove it this way
            link.linked_to.apposita.remove(anonymous_fragment)
        return redirect(self.get_success_url())


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
    template_name = 'research/fragment_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'editing': 'commentary',
        })
        return context


class AnonymousFragmentUpdateCommentaryView(AnonymousFragmentUpdateView):
    model = AnonymousFragment
    form_class = AnonymousFragmentCommentaryForm
    permission_required = ('research.change_fragment',)
    template_name = 'research/anonymousfragment_detail.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'editing': 'commentary',
        })
        return context


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
            FragmentLink.objects.get_or_create(**data)

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
