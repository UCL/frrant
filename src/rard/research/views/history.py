from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.views.generic import ListView


class HistoryListView(LoginRequiredMixin, ListView):
    paginate_by = 10
    template_name = 'research/history_list.html'

    @property
    def model(self):
        model_name = self.kwargs.get('model_name')
        return apps.get_model(app_label='research', model_name=model_name)

    def get_object(self):
        try:
            return self.model.objects.get(pk=self.kwargs.get('pk'))
        except ObjectDoesNotExist:
            raise Http404

    def get_context_data(self, *args, **kwargs):
        queryset = kwargs.pop('object_list', None)
        if queryset is None:
            self.object_list = self.get_queryset()

        context = super().get_context_data(*args, **kwargs)
        context.update({
            'object': self.get_object(),
            'diff_item': int(self.request.GET.get('diff', 0)) or None
        })
        return context

    def get_queryset(self):
        # actually get the history items
        return self.get_object().history.all()

    def post(self, *args, **kwargs):
        history_item_id = self.request.POST.get('history_item_id', None)
        # model_name = self.request.POST.get('model_name', None)

        if history_item_id:
            # reverting to a previous version
            try:
                obj = self.get_object()
                history_item = obj.history.get(pk=history_item_id)
                if 'revert' in self.request.POST:
                    with transaction.atomic():
                        history_item.instance.save()
                        new_item = obj.history.first()
                        new_item.history_change_reason = 'reverted'
                        new_item.save()

            except (ObjectDoesNotExist):
                pass

        return HttpResponseRedirect(self.request.path)
