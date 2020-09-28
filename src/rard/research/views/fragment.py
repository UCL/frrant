from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import CitingWorkForm, FragmentForm, OriginalTextForm
from rard.research.models import Fragment


class FragmentCreateView(LoginRequiredMixin, TemplateView):
    template_name = 'research/fragment_create_form.html'

    def get_forms(self):
        forms = {
            'original_text': OriginalTextForm(data=self.request.POST or None),
            'fragment': FragmentForm(data=self.request.POST or None),
            'new_citing_work': CitingWorkForm(data=self.request.POST or None)
        }
        return forms

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'forms': self.get_forms(),
        })
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        forms = context['forms']
        print('POST data %s' % self.request.POST)
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
            fragment_form = forms['fragment']
            fragment = fragment_form.save()

            original_text = forms['original_text'].save(commit=False)
            original_text.owner = fragment

            if create_citing_work:
                original_text.citing_work = forms['new_citing_work'].save()

            original_text.save()

            return redirect(
                reverse('fragment:detail', kwargs={'pk': fragment.pk})
            )

        # reset the changes we made to required fields 
        # and invite the user to try again
        forms['new_citing_work'].set_required(False)
        forms['original_text'].set_citing_work_required(False)

        return self.render_to_response(context)


class FragmentListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment


class FragmentDetailView(LoginRequiredMixin, DetailView):
    model = Fragment


class FragmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Fragment
    success_url = reverse_lazy('fragment:list')


class FragmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Fragment
    form_class = FragmentForm

    def get_success_url(self, *args, **kwargs):
        return reverse('fragment:detail', kwargs={'pk': self.object.pk})
