from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from rard.research.models import Fragment


class HomeView(TemplateView):
    def get_template_names(self):
        if not self.request.user.is_authenticated:
            return ["pages/front.html"]
        else:
            return ["research/home.html"]


class AnonymousListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ("research.view_fragment",)
    template_name = "research/anonymous_list.html"

    def get_queryset(self):
        from django.db.models import F

        return (
            super()
            .get_queryset()
            .filter(is_anonymous=True)
            .annotate(topic=F("topics__name"))
            .order_by("topic", "topiclink__order")
        )


def render_editor_modal_template(request):
    import re

    from rard.utils.context_processors import symbols_context

    context = symbols_context(request)
    source_page = request.GET.get("sourcePage")
    source_page = source_page.replace("-", "")
    pattern = r"/(\w+)/(\d+)/"
    match = re.search(pattern, source_page)
    if match:
        context["object_class"] = match.group(1)
        context["object_id"] = int(match.group(2))

    return render(
        request, "research/partials/render_editor_modal_base.html", context=context
    )
