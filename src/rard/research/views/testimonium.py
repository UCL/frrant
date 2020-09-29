from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import TestimoniumForm
from rard.research.models import Testimonium
from rard.research.views.fragment import HistoricalBaseCreateView


class TestimoniumCreateView(HistoricalBaseCreateView):
    form_class = TestimoniumForm
    success_url_name = 'testimonium:detail'
    title = 'Create Testimonium'


class TestimoniumListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Testimonium


class TestimoniumDetailView(LoginRequiredMixin, DetailView):
    model = Testimonium


@method_decorator(require_POST, name='dispatch')
class TestimoniumDeleteView(LoginRequiredMixin, DeleteView):
    model = Testimonium
    success_url = reverse_lazy('testimonium:list')


class TestimoniumUpdateView(LoginRequiredMixin, UpdateView):
    model = Testimonium
    form_class = TestimoniumForm

    def get_success_url(self, *args, **kwargs):
        return reverse('testimonium:detail', kwargs={'pk': self.object.pk})
