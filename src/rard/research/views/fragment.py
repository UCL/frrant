from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView, TemplateView
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (CitingWorkForm, FragmentForm,
                                 FragmentLinkWorkForm, OriginalTextForm)
from rard.research.models import Fragment, Work, Book
from rard.research.models.base import FragmentLink


class HistoricalBaseCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'research/base_create_form.html'

    def get_forms(self):
        forms = {
            'original_text': OriginalTextForm(data=self.request.POST or None),
            'object': self.form_class(data=self.request.POST or None),
            'new_citing_work': CitingWorkForm(data=self.request.POST or None)
        }
        return forms

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'forms': self.get_forms(),
            'title': self.title
        })
        return context

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
            # save the objects here
            object_form = forms['object']
            saved_object = object_form.save()

            original_text = forms['original_text'].save(commit=False)
            original_text.owner = saved_object

            if create_citing_work:
                original_text.citing_work = forms['new_citing_work'].save()

            original_text.save()

            return redirect(
                reverse(self.success_url_name, kwargs={'pk': saved_object.pk})
            )

        # reset the changes we made to required fields
        # and invite the user to try again
        forms['new_citing_work'].set_required(False)
        forms['original_text'].set_citing_work_required(False)

        return self.render_to_response(context)


class FragmentCreateView(PermissionRequiredMixin, HistoricalBaseCreateView):
    form_class = FragmentForm
    success_url_name = 'fragment:detail'
    title = 'Create Fragment'
    permission_required = ('research.add_fragment',)


class FragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ('research.view_fragment',)


class FragmentDetailView(
        LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Fragment
    permission_required = ('research.view_fragment',)


@method_decorator(require_POST, name='dispatch')
class FragmentDeleteView(
        LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Fragment
    success_url = reverse_lazy('fragment:list')
    permission_required = ('research.delete_fragment',)


class FragmentUpdateView(
        LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Fragment
    form_class = FragmentForm
    permission_required = ('research.change_fragment',)

    def get_success_url(self, *args, **kwargs):
        return reverse('fragment:detail', kwargs={'pk': self.object.pk})


class FragmentUpdateAntiquariansView(FragmentUpdateView):
    # use a different template showing fewer fields
    template_name = 'research/fragment_antiquarians_form.html'


class FragmentAddWorkLinkView(
        LoginRequiredMixin, PermissionRequiredMixin, FormView):
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
                pass
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


class FragmentRemoveLinkView(
        LoginRequiredMixin, PermissionRequiredMixin, RedirectView):

    # base class for both remove work and remove book from a fragment
    permission_required = ('research.edit_fragment',)

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
