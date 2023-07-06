from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import (
    BookForm,
    BookIntroductionForm,
    WorkForm,
    WorkIntroductionForm,
)
from rard.research.models import Book, TextObjectField, Work
from rard.research.views.mixins import CanLockMixin, CheckLockMixin


class WorkListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Work
    permission_required = ("research.view_work",)


class WorkDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = Work
    permission_required = ("research.view_work",)

    def get_context_data(self, **kwargs):
        """use work model method get_ordered_materials to retrieve a dictionary of all fragments,
        testimonia and apposita grouped by book and add it to the context"""

        context = super().get_context_data(**kwargs)
        work = self.get_object()

        ordered_materials = work.get_ordered_materials()

        cleaned_ordered_materials = {
            book: materials
            for book, materials in ordered_materials.items()
            if any([bool(item_list) for item_list in materials.values()])
        }
        context["ordered_materials"] = ordered_materials
        context["cleaned_materials"] = cleaned_ordered_materials
        return context


def add_new_books_to_work(work, form):
    for book in form.cleaned_data["books"]:
        Book(
            number=book.get("num"),
            subtitle=book.get("title", ""),
            date_range=book.get("date", ""),
            order_year=book.get("order"),
            work=work,
        ).save()


class WorkCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Work
    form_class = WorkForm
    success_url = reverse_lazy("work:list")
    permission_required = ("research.add_work", "research.add_book")

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        rtn = super().form_valid(form)
        for a in form.cleaned_data["antiquarians"]:
            a.works.add(self.object)
        add_new_books_to_work(self.object, form)
        return rtn


class WorkUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Work
    form_class = WorkForm
    permission_required = ("research.change_work",)

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        work = form.save(commit=False)
        if "antiquarians" in form.cleaned_data:
            updated = form.cleaned_data["antiquarians"]
            existing = work.antiquarian_set.all()
            to_remove = [a for a in existing if a not in updated]
            to_add = [a for a in updated if a not in existing]
            for a in to_remove:
                a.works.remove(work)
            for a in to_add:
                a.works.add(work)
            add_new_books_to_work(work, form)
        return super().form_valid(form)


class WorkUpdateIntroductionView(WorkUpdateView):
    model = Work
    form_class = WorkIntroductionForm
    permission_required = ("research.change_work",)
    template_name = "research/work_detail.html"

    def create_intro_if_does_not_exist(self, *args, **kwargs):
        # If a TOF is not created for the introduction an error will be
        # thrown when trying to save as it will try to save something that
        # does not exist
        work = self.get_object()
        if work.introduction is None:
            work.introduction = TextObjectField.objects.create(content="")
            work.save()

    def dispatch(self, request, *args, **kwargs):
        self.create_intro_if_does_not_exist()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "editing": "introduction",
            }
        )
        return context


@method_decorator(require_POST, name="dispatch")
class WorkDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = Work
    success_url = reverse_lazy("work:list")
    permission_required = ("research.delete_work",)


class BookCreateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView
):
    # the view attribute that needs to be checked for a lock
    check_lock_object = "work"
    model = Book
    form_class = BookForm
    permission_required = (
        "research.change_work",
        "research.add_book",
    )

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_work()
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.work.pk})

    def get_work(self, *args, **kwargs):
        if not getattr(self, "work", False):
            self.work = get_object_or_404(Work, pk=self.kwargs.get("pk"))
        return self.work

    def form_valid(self, form):
        book = form.save(commit=False)
        book.work = self.get_work()
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "work": self.get_work(),
            }
        )
        return context


class BookUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    # the view attribute that needs to be checked for a lock
    check_lock_object = "work"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_work()
        return super().dispatch(request, *args, **kwargs)

    def get_work(self, *args, **kwargs):
        if not getattr(self, "work", False):
            self.work = self.get_object().work
        return self.work

    model = Book
    form_class = BookForm
    permission_required = (
        "research.change_work",
        "research.change_book",
    )

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.object.work.pk})

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "work": self.get_work(),
            }
        )
        return context


class BookUpdateIntroductionView(BookUpdateView):
    model = Book
    form_class = BookIntroductionForm
    permission_required = ("research.change_book",)
    template_name = "research/book_form.html"

    def create_intro_if_does_not_exist(self, *args, **kwargs):
        # If a TOF is not created for the introduction an error will be
        # thrown when trying to save as it will try to save something that
        # does not exist
        book = self.get_object()
        if book.introduction is None:
            book.introduction = TextObjectField.objects.create(content="")
            book.save()

    def dispatch(self, request, *args, **kwargs):
        self.create_intro_if_does_not_exist()
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "editing": "introduction",
                "change_work": True,
                "change_book": True,
                "has_object_lock": True,
                "instance": self.get_object(),
            }
        )
        return context


@method_decorator(require_POST, name="dispatch")
class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = (
        "research.change_work",
        "research.delete_book",
    )

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.object.work.pk})
