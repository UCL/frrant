from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (AntiquarianForm, AntiquarianUpdateWorksForm,
                                 WorkForm)
from rard.research.models import Antiquarian, Work
from rard.research.views.mixins import DateOrderMixin


class AntiquarianListView(
        DateOrderMixin, LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Antiquarian
    permission_required = ('research.view_antiquarian',)


class AntiquarianDetailView(
        LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Antiquarian
    permission_required = ('research.view_antiquarian',)

    def post(self, *args, **kwargs):

        link_pk = self.request.POST.get('link_id', None)
        object_type = self.request.POST.get('object_type', None)
        if link_pk and object_type:
            from rard.research.models.base import FragmentLink, TestimoniumLink
            model_classes = {
                'fragment': FragmentLink,
                'testimonium': TestimoniumLink,
            }
            try:
                model_class = model_classes[object_type]
                link = model_class.objects.get(pk=link_pk)
                if 'up' in self.request.POST:
                    link.up()
                elif 'down' in self.request.POST:
                    link.down()
            except (FragmentLink.DoesNotExist, KeyError):
                pass
        return HttpResponseRedirect(self.request.path)


class AntiquarianCreateView(
        LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Antiquarian
    permission_required = ('research.add_antiquarian',)
    form_class = AntiquarianForm

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


class AntiquarianUpdateView(
        LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Antiquarian
    permission_required = ('research.change_antiquarian',)
    form_class = AntiquarianForm

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


@method_decorator(require_POST, name='dispatch')
class AntiquarianDeleteView(
        LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Antiquarian
    permission_required = ('research.delete_antiquarian',)
    success_url = reverse_lazy('antiquarian:list')


class AntiquarianWorksUpdateView(
        LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Antiquarian
    form_class = AntiquarianUpdateWorksForm
    permission_required = ('research.change_antiquarian',)
    template_name = 'research/antiquarian_works_form.html'

    def get_success_url(self, *args, **kwargs):
        return reverse('antiquarian:detail', kwargs={'pk': self.object.pk})


class AntiquarianWorkCreateView(
        LoginRequiredMixin, PermissionRequiredMixin, CreateView):
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
        self.antiquarian = self.get_antiquarian()
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
