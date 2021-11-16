from itertools import groupby

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from rard.research.forms import BookForm, WorkForm
from rard.research.models import AnonymousFragment, Book, Fragment, Testimonium, Work
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
        """Add a dictionary to context data called ordered materials.
        For each book in this work, add the book and a list of associated material
        ordered by definite/possible boolean, then by material type; e.g.:
        ordered_materials = {'book1': {'definite': [F1, T1, A1],
                                       'possible': [F2, T2, A2]
                                       },
                             'book2': {...},
                            }
        """
        context = super().get_context_data(**kwargs)
        work = self.get_object()
        books = work.book_set.all()
        # Empty structure with space for materials with unknown book
        ordered_materials = {
            book.__str__(): {"definite": [], "possible": []}
            for book in list(books) + ["unknown"]
        }

        def inflate(query_list, pk_field, model, new_key):
            """For each item in the query list, use the field value and the model
            to add the actual object to the dictionary"""
            for item in query_list:
                item[new_key] = (
                    model.objects.get(pk=item[pk_field]) if item[pk_field] else None
                )
            return query_list

        def make_grouped_dict(query_list):
            """Take a list of dictionaries each containing 'book' and 'definite' keys
            and create a new dictionary where the keys are books, each value
            is another dictionary containing separate object lists for definite
            and possible links; e.g.:
            query_list = [{'book':'book1','definite'true','object':F1},
                          {'book':'book1','definite'false','object':F2},
                          {'book':'book1','definite'true','object':F3},
                          {'book':'book1','definite'false','object':F4},
                          {'book':'book1','definite'true','object':F5},
                          {'book':'book1','definite'false','object':F6}]
            grouped_dict = {'book1': {'true': [F1,F3,F5],'false':[F2,F4,F6]}}"""
            grouped_dict = {
                k[0]: {k[1]: [f["object"] for f in v]}
                for k, v in groupby(query_list, lambda x: [x["book"], x["definite"]])
            }
            return grouped_dict

        def add_to_ordered_materials(grouped_dict):
            for book, materials in grouped_dict.items():
                if book:
                    ordered_materials[book.__str__()]["definite"] += materials.get(
                        True, []
                    )
                    ordered_materials[book.__str__()]["possible"] += materials.get(
                        False, []
                    )
                else:  # If book is None it's unknown
                    ordered_materials["unknown"]["definite"] += materials.get(True, [])
                    ordered_materials["unknown"]["possible"] += materials.get(False, [])

        # For each fragmentlink, get definite, book (can be None), and fragment pk
        # Needs to be ordered by book then definite for make_grouped_dict to work
        fragments = list(
            work.antiquarian_work_fragmentlinks.values(
                "definite", "book", pk=F("fragment__pk")
            ).order_by("book", "-definite")
        )
        fragments = inflate(
            inflate(fragments, "pk", Fragment, "object"), "book", Book, "book"
        )
        fragments = make_grouped_dict(fragments)
        add_to_ordered_materials(fragments)

        # Same for testimonia via work_testimoniumlinks
        testimonia = list(
            work.antiquarian_work_testimoniumlinks.values(
                "definite", "book", pk=F("testimonium__pk")
            ).order_by("book", "-definite")
        )
        testimonia = inflate(
            inflate(testimonia, "pk", Testimonium, "object"), "book", Book, "book"
        )
        testimonia = make_grouped_dict(testimonia)
        add_to_ordered_materials(testimonia)

        # Finally for apposita
        apposita = list(
            work.antiquarian_work_appositumfragmentlinks.values(
                "definite", "book", pk=F("anonymous_fragment__pk")
            ).order_by("book", "-definite")
        )
        apposita = inflate(
            inflate(apposita, "pk", AnonymousFragment, "object"), "book", Book, "book"
        )
        apposita = make_grouped_dict(apposita)
        add_to_ordered_materials(apposita)

        context["ordered_materials"] = ordered_materials
        return ordered_materials


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


@method_decorator(require_POST, name="dispatch")
class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    permission_required = (
        "research.change_work",
        "research.delete_book",
    )

    def get_success_url(self, *args, **kwargs):
        return reverse("work:detail", kwargs={"pk": self.object.work.pk})
