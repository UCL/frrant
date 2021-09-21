from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.edit import DeleteView, FormMixin

from rard.research.forms import CommentForm
from rard.research.models import Comment, TextObjectField


@method_decorator(require_POST, name="dispatch")
class CommentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Comment
    permission_required = ("research.delete_comment",)

    def get_success_url(self, *args, **kwargs):
        # send to the refering page. Should have one as
        # delete must be done using post
        return self.request.META.get("HTTP_REFERER", reverse("home"))

    def get_queryset(self):
        qs = super().get_queryset()
        # only allow own comments to be deleted
        return qs.filter(user=self.request.user)


@method_decorator(
    permission_required("research.add_comment", raise_exception=True), name="post"
)
class CommentListViewBase(
    LoginRequiredMixin, PermissionRequiredMixin, FormMixin, ListView
):
    paginate_by = 10
    model = Comment
    form_class = CommentForm
    permission_required = ("research.view_comment",)

    def get_parent_object(self):
        if not getattr(self, "parent_object", False):
            self.parent_object = get_object_or_404(
                self.parent_object_class, pk=self.kwargs.get("pk")
            )
        return self.parent_object

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return self.request.path

    def get_context_data(self, *args, **kwargs):
        queryset = kwargs.pop("object_list", None)
        if queryset is None:
            self.object_list = self.get_queryset()

        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "parent_object": self.get_parent_object(),
            }
        )
        return context

    def get_queryset(self):
        parent_object = self.get_parent_object()
        qs = super().get_queryset()
        return qs.filter(object_id=parent_object.pk)

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.user = self.request.user
        comment.parent = self.get_parent_object()
        comment.save()
        return super().form_valid(form)


class TextObjectFieldCommentListView(CommentListViewBase):
    parent_object_class = TextObjectField
    template_name = "research/text_object_comment_list.html"
