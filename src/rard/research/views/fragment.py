from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import CitingWorkForm, FragmentForm, OriginalTextForm
from rard.research.models import Fragment


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


class FragmentCreateView(HistoricalBaseCreateView):
    form_class = FragmentForm
    success_url_name = 'fragment:detail'
    title = 'Create Fragment'


class FragmentListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment


class FragmentDetailView(LoginRequiredMixin, DetailView):
    model = Fragment


@method_decorator(require_POST, name='dispatch')
class FragmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Fragment
    success_url = reverse_lazy('fragment:list')


class FragmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Fragment
    form_class = FragmentForm

    def get_success_url(self, *args, **kwargs):
        return reverse('fragment:detail', kwargs={'pk': self.object.pk})
