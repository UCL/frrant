from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import TestimoniumForm
from rard.research.models import Testimonium
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
