from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (AntiquarianCreateForm, AntiquarianDetailsForm,
                                 AntiquarianIntroductionForm,
                                 AntiquarianUpdateWorksForm, WorkForm)
from rard.research.models import (Antiquarian, AntiquarianConcordance,
                                  BibliographyItem, Work)
from rard.research.views.mixins import (CanLockMixin, CheckLockMixin,
                                        DateOrderMixin)


class AntiquarianListView(
        DateOrderMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Antiquarian
    permission_required = ('research.view_antiquarian',)


class AntiquarianDetailView(
        CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Antiquarian
    permission_required = ('research.view_antiquarian',)

    def post(self, *args, **kwargs):

        link_pk = self.request.POST.get('link_id', None)
        work_pk = self.request.POST.get('work_id', None)
        antiquarian_pk = self.request.POST.get('antiquarian_id', None)
        object_type = self.request.POST.get('object_type', None)
        if work_pk:
            # moving a work up in the collection
            try:
                work = Work.objects.get(pk=work_pk)
                antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
                link = antiquarian.worklink_set.get(work=work)

                if 'work_up' in self.request.POST:
                    link.up()
                elif 'work_down' in self.request.POST:
                    link.down()
            except (Work.DoesNotExist, KeyError):
                pass

        if link_pk and object_type:
            from rard.research.models.base import (AppositumFragmentLink,
                                                   FragmentLink,
                                                   TestimoniumLink)
            model_classes = {
                'fragment': FragmentLink,
                'anonymous_fragment': AppositumFragmentLink,
                'testimonium': TestimoniumLink,
            }
            try:
                model_class = model_classes[object_type]
                link = model_class.objects.get(pk=link_pk)
                if 'up_by_work' in self.request.POST:
                    link.up_by_work()
                elif 'down_by_work' in self.request.POST:
                    link.down_by_work()

            except (ObjectDoesNotExist, KeyError):
                pass
        return HttpResponseRedirect(self.request.path)


class AntiquarianCreateView(
        LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Antiquarian
    permission_required = ('research.add_antiquarian',)
    form_class = AntiquarianCreateForm

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


class AntiquarianUpdateView(LoginRequiredMixin, CheckLockMixin,
                            PermissionRequiredMixin, UpdateView):
    model = Antiquarian
    permission_required = ('research.change_antiquarian',)
    form_class = AntiquarianDetailsForm

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


class AntiquarianUpdateIntroductionView(LoginRequiredMixin, CheckLockMixin,
                                        PermissionRequiredMixin, UpdateView):
    model = Antiquarian
    permission_required = ('research.change_antiquarian',)
    form_class = AntiquarianIntroductionForm
    template_name = 'research/antiquarian_detail.html'

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'antiquarian:detail',
            kwargs={'pk': self.object.pk}
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'editing': 'introduction',
        })
        return context


@method_decorator(require_POST, name='dispatch')
class AntiquarianDeleteView(CheckLockMixin, LoginRequiredMixin,
                            PermissionRequiredMixin, DeleteView):
    model = Antiquarian
    permission_required = ('research.delete_antiquarian',)
    success_url = reverse_lazy('antiquarian:list')


class AntiquarianBibliographyCreateView(CheckLockMixin, LoginRequiredMixin,
                                        PermissionRequiredMixin, CreateView):

    # the view attribute that needs to be checked for a lock
    check_lock_object = 'antiquarian'

    model = BibliographyItem
    fields = ('authors', 'author_surnames', 'year', 'title',)
    permission_required = (
        'research.change_antiquarian',
        'research.add_bibliographyitem',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'antiquarian:detail', kwargs={'pk': self.antiquarian.pk}
        )

    def dispatch(self, *args, **kwargs):
        # need to ensure the lock-checked attribute is initialised in dispatch
        self.get_antiquarian()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        # self.antiquarian = self.get_antiquarian()
        item = form.save(commit=False)
        item.parent = self.antiquarian
        # self.antiquarian.bibliography_items.add(item)
        return super().form_valid(form)

    def get_antiquarian(self, *args, **kwargs):
        if not getattr(self, 'antiquarian', False):
            self.antiquarian = get_object_or_404(
                Antiquarian,
                pk=self.kwargs.get('pk')
            )
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'antiquarian': self.antiquarian,
        })
        return context


class AntiquarianWorksUpdateView(CheckLockMixin, LoginRequiredMixin,
                                 PermissionRequiredMixin, UpdateView):
    model = Antiquarian
    form_class = AntiquarianUpdateWorksForm
    permission_required = ('research.change_antiquarian',)
    template_name = 'research/antiquarian_works_form.html'

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


class AntiquarianWorkCreateView(CheckLockMixin, LoginRequiredMixin,
                                PermissionRequiredMixin, CreateView):

    # the view attribute that needs to be checked for a lock
    check_lock_object = 'antiquarian'

    model = Work
    form_class = WorkForm
    permission_required = (
        'research.change_antiquarian',
        'research.add_work',
    )

    def get_success_url(self, *args, **kwargs):
        return reverse(
            'antiquarian:detail', kwargs={'pk': self.antiquarian.pk}
        )

    def dispatch(self, *args, **kwargs):
        # need to ensure the lock-checked attribute is initialised in dispatch
        self.get_antiquarian()
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        # self.antiquarian = self.get_antiquarian()
        work = form.save()
        self.antiquarian.works.add(work)
        return super().form_valid(form)

    def get_antiquarian(self, *args, **kwargs):
        if not getattr(self, 'antiquarian', False):
            self.antiquarian = get_object_or_404(
                Antiquarian,
                pk=self.kwargs.get('pk')
            )
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'antiquarian': self.antiquarian,
        })
        return context


class AntiquarianConcordanceCreateView(CheckLockMixin, LoginRequiredMixin,
                                       PermissionRequiredMixin, CreateView):

    check_lock_object = 'antiquarian'

    # create a concordance for an original text
    model = AntiquarianConcordance
    permission_required = ('research.add_antiquarianconcordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_antiquarian()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()

    def form_valid(self, form):
        concordance = form.save(commit=False)
        concordance.antiquarian = self.get_antiquarian()
        return super().form_valid(form)

    def get_antiquarian(self, *args, **kwargs):
        if not getattr(self, 'antiquarian', False):
            self.antiquarian = get_object_or_404(
                Antiquarian,
                pk=self.kwargs.get('pk')
            )
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'antiquarian': self.get_antiquarian(),
        })
        return context


class AntiquarianConcordanceUpdateView(CheckLockMixin, LoginRequiredMixin,
                                       PermissionRequiredMixin, UpdateView):

    check_lock_object = 'antiquarian'

    model = AntiquarianConcordance
    permission_required = ('research.change_antiquarianconcordance',)
    fields = ('source', 'identifier')

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.antiquarian = self.get_object().antiquarian
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'antiquarian': self.antiquarian,
        })
        return context

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class AntiquarianConcordanceDeleteView(CheckLockMixin, LoginRequiredMixin,
                                       PermissionRequiredMixin, DeleteView):
    check_lock_object = 'antiquarian'

    model = AntiquarianConcordance
    permission_required = ('research.delete_antiquarianconcordance',)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.antiquarian = self.get_object().antiquarian
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return self.object.antiquarian.get_absolute_url()
