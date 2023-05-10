from django.contrib.auth.context_processors import PermWrapper
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.db.models import F
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import resolve, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import FormView, ListView, TemplateView, View
from django.views.generic.base import RedirectView
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, UpdateView

from rard.research.forms import (
    AnonymousFragmentCommentaryForm,
    AnonymousFragmentForm,
    AppositumFragmentLinkForm,
    AppositumGeneralLinkForm,
    FragmentAntiquariansForm,
    FragmentCommentaryForm,
    FragmentForm,
    FragmentLinkWorkForm,
    OriginalTextForm,
    ReferenceFormset,
)
from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    CitingAuthor,
    CitingWork,
    Fragment,
    Topic,
    Work,
)
from rard.research.models.base import AppositumFragmentLink, FragmentLink
from rard.research.models.fragment import AnonymousTopicLink
from rard.research.views.mixins import (
    CanLockMixin,
    CheckLockMixin,
    GetWorkLinkRequestDataMixin,
)
from rard.utils.convertors import (
    convert_anonymous_fragment_to_fragment,
    convert_unlinked_fragment_to_anonymous_fragment,
)


class OriginalTextCitingWorkView(LoginRequiredMixin, TemplateView):
    def get_forms(self):
        forms = {
            "original_text": OriginalTextForm(
                citing_author=self.get_citing_author_from_form(),
                citing_work=self.get_citing_work_from_form(),
                data=self.request.POST or None,
            ),
        }
        return forms

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "forms": self.get_forms(),
                "citing_author": self.get_citing_author_from_form(),
                "citing_work": self.get_citing_work_from_form(),
            }
        )
        return context

    def forms_valid(self, form):
        return redirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        forms = context["forms"]

        if (
            "create_object" in self.request.POST
            or "then_add_links" in self.request.POST
            or "then_add_apparatus_criticus" in self.request.POST
        ):
            # now check the forms using the form validation
            forms_valid = all([x.is_bound and x.is_valid() for x in forms.values()])
            if forms_valid:
                return self.forms_valid(forms)

        else:
            for _, form in forms.items():
                form.errors.clear()

        return self.render_to_response(context)

    def get_citing_author_from_form(self, *args, **kwargs):
        # look for author in the GET or POST parameters
        self.citing_author = None
        if self.request.method == "GET":
            author_pk = self.request.GET.get("citing_author", None)
        elif self.request.method == "POST":
            author_pk = self.request.POST.get("citing_author", None)
        if author_pk:
            try:
                self.citing_author = CitingAuthor.objects.get(pk=author_pk)
            except CitingAuthor.DoesNotExist:
                raise Http404
        return self.citing_author

    def get_citing_work_from_form(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.citing_work = None
        if self.request.method == "GET":
            author_pk = self.request.GET.get("citing_work", None)
        elif self.request.method == "POST":
            author_pk = self.request.POST.get("citing_work", None)
        if author_pk:
            try:
                self.citing_work = CitingWork.objects.get(pk=author_pk)
            except CitingWork.DoesNotExist:
                raise Http404
        return self.citing_work


class HistoricalBaseCreateView(OriginalTextCitingWorkView):
    template_name = "research/base_create_form.html"

    def get_forms(self):
        forms = super().get_forms()
        forms["object"] = self.form_class(data=self.request.POST or None)
        forms["references"] = ReferenceFormset(data=self.request.POST or None)
        return forms

    def post_process_saved_object(self, saved_object):
        # override this to do extra things to the saved
        # object before redirect
        pass

    def forms_valid(self, forms):
        # save the objects here
        object_form = forms["object"]
        self.saved_object = object_form.save()

        original_text = forms["original_text"].save(commit=False)
        original_text.owner = self.saved_object

        original_text.save()

        references = forms["references"]
        references.instance = original_text
        references.save()

        self.post_process_saved_object(self.saved_object)

        if (
            "then_add_links" in self.request.POST
            or "then_add_apparatus_criticus" in self.request.POST
        ):
            # lock the object
            self.saved_object.lock(self.request.user)

        return redirect(self.get_success_url())

    def get_add_links_url(self):
        return reverse(self.add_links_url_name, kwargs={"pk": self.saved_object.pk})

    def get_success_url(self):
        if "then_add_links" in self.request.POST:
            # go to the 'add links' page
            return self.get_add_links_url()

        if "then_add_apparatus_criticus" in self.request.POST:
            # load the update view for the original text
            # (but needs to be in the correct namespace for the parent)
            namespace = resolve(self.request.path_info).namespace
            if self.saved_object.original_texts.count() > 0:
                return reverse(
                    "%s:update_original_text" % namespace,
                    kwargs={"pk": self.saved_object.original_texts.first().pk},
                )

        return reverse(self.success_url_name, kwargs={"pk": self.saved_object.pk})


class FragmentCreateView(PermissionRequiredMixin, HistoricalBaseCreateView):
    form_class = FragmentForm
    success_url_name = "fragment:detail"
    add_links_url_name = "fragment:add_work_link"
    title = "Create Fragment"
    permission_required = ("research.add_fragment",)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"title": self.title})
        return context


class AnonymousFragmentCreateView(FragmentCreateView):
    form_class = AnonymousFragmentForm
    success_url_name = "anonymous_fragment:detail"
    title = "Create Anonymous Fragment"
    permission_required = ("research.add_anonymousfragment",)

    def get_add_links_url(self):
        link_type = self.request.POST.get("then_add_links", None)
        url_name = "link_fragment" if link_type == "fragment" else "link"
        return reverse(
            "anonymous_fragment:{}".format(url_name),
            kwargs={"pk": self.saved_object.pk},
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "title": self.title,
                "is_anonymous_fragment": True,
            }
        )
        return context


class AppositumCreateView(AnonymousFragmentCreateView):
    title = "Create Appositum"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({"title": self.title, "owner_for": self.get_owner_for()})
        return context

    def post_process_saved_object(self, saved_object):
        # we need to link our anon fragment to the
        # new owner
        new_owner = self.get_owner_for()
        if isinstance(new_owner, Fragment):
            new_owner.apposita.add(saved_object)
        elif isinstance(new_owner, Antiquarian):
            AppositumFragmentLink.objects.get_or_create(
                anonymous_fragment=saved_object, antiquarian=new_owner
            )
        elif isinstance(new_owner, Work):
            # loop through the owners of the work
            # and create links for each
            for antiquarian in new_owner.antiquarian_set.all():
                AppositumFragmentLink.objects.get_or_create(
                    anonymous_fragment=saved_object,
                    antiquarian=antiquarian,
                    work=new_owner,
                )

    def get_owner_for(self):
        if getattr(self, "owner_for", False):
            return self.owner_for

        what = self.kwargs.get("slug")
        owner_pk = self.kwargs.get("owner_pk")

        lookup = {
            "antiquarian": Antiquarian,
            "work": Work,
            "fragment": Fragment,
        }
        obj_class = lookup.get(what, None)

        if not obj_class:
            raise Http404
        try:
            self.owner_for = obj_class.objects.get(pk=owner_pk)
        except ObjectDoesNotExist:
            raise Http404

        return self.owner_for


class FragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    paginate_by = 10
    model = Fragment
    permission_required = ("research.view_fragment",)


class AnonymousFragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = AnonymousTopicLink
    permission_required = "research.view_fragment"
    template_name = "research/anonymousfragment_list.html"

    def get_selected_topic(self):
        topic_id = self.request.GET.get("selected_topic", None)
        if not topic_id:
            topic_id = Topic.objects.get(order=0).id
        return Topic.objects.get(id=topic_id)

    def order_object_list_by_reference(self, qs):
        """When ordering by reference order, some of the fragments
        have multiple original texts and therefore two reference_orders.
        We want duplicate objects to appear in the queryset for each
        original text and we want the citing info for each to be displayed
        differently on the rendered page. This can be achieved by annotating
        the queryset with related original text's citing authors, which can
        then be passed to the show_citing_info template tag.


        For example:
        > anonymous_f1.get_citing_display(citing_author_1)
        'Charisius, ars grammatica 1.2.3
        (also = Aulus Gellius, Noctes Atticae 1.19.cap., 1-11)'
        > anonymous_f1.get_citing_display(citing_author_2)
        'Aulus Gellius, Noctes Atticae 1.19.cap., 1-11
        (also = Charisius, ars grammatica 1.2.3)'
        """

        # Create duplicate entries for each original text
        # with different citing_author annotations

        qs = qs.annotate(
            citing_author=F("fragment__original_texts__citing_work__author")
        )
        # Sort by reference order
        return qs.order_by("fragment__original_texts__reference_order")

    def get_context_data(self, *args, **kwargs):
        context_data = super().get_context_data(*args, **kwargs)

        # Add list of all topics to context
        topic_qs = Topic.objects.all()
        topics = []
        for i in topic_qs:
            topics.append([i.id, i.name])
        context_data["topics"] = topics
        context_data["selected_topic"] = self.get_selected_topic()

        # Get display order: by_topic (default) or by_reference
        display_order = self.request.GET.get("display_order", "by_topic")
        context_data["display_order"] = display_order

        # Reorder object list if displaying by reference order
        if display_order == "by_reference":
            context_data["object_list"] = self.order_object_list_by_reference(
                context_data["object_list"]
            )

        return context_data

    def get_queryset(self, topic=None):
        """Queryset should include all anonymous topic links related
        to a give topic and should not include apposita.

        If no topic_id is given we'll get the topic from the request.
        If none given there, choose the topic with the lowest order
        as default."""
        topic = topic or self.get_selected_topic()
        qs = (
            super()
            .get_queryset()
            .filter(
                fragment__appositumfragmentlinks_from__isnull=True,
                topic=topic,
            )
        ).order_by("order")

        return qs


class UnlinkedFragmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Fragment
    permission_required = "research.view_fragment"
    template_name = "research/unlinkedfragment_list.html"

    def get_queryset(self):
        """Queryset should include all unlinked fragments."""
        qs = Fragment.objects.all().filter(
            linked_antiquarians=None,
        )

        return qs


class AddAppositumGeneralLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    check_lock_object = "anonymous_fragment"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = "research/add_appositum_link.html"
    form_class = AppositumGeneralLinkForm
    permission_required = (
        "research.change_anonymousfragment",
        "research.add_appositumfragmentlink",
    )

    def get_success_url(self, *args, **kwargs):
        if "another" in self.request.POST:
            return self.request.path
        return reverse(
            "anonymous_fragment:detail", kwargs={"pk": self.get_anonymous_fragment().pk}
        )

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, "anonymous_fragment", False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment, pk=self.kwargs.get("pk")
            )
        return self.anonymous_fragment

    def form_valid(self, form):
        data = form.cleaned_data
        work = data["work"]
        book = data["book"]
        exclusive = data["exclusive"]

        antiquarian = data["antiquarian"]
        # though they browsed to the work via the antiquarian,
        # if there are multiple authors of that work we need to
        # link them all
        link_to_antiquarians = (
            work.antiquarian_set.all() if work and not exclusive else [antiquarian]
        )

        for antiquarian in link_to_antiquarians:
            data["anonymous_fragment"] = self.get_anonymous_fragment()
            data["antiquarian"] = antiquarian
            data["work"] = work
            data["book"] = book
            AppositumFragmentLink.objects.get_or_create(**data)

        return super().form_valid(form)

    def get_work(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.work = None
        if self.request.method == "GET":
            work_pk = self.request.GET.get("work", None)
        elif self.request.method == "POST":
            work_pk = self.request.POST.get("work", None)
        if work_pk:
            try:
                self.work = Work.objects.get(pk=work_pk)
            except Work.DoesNotExist:
                raise Http404
        return self.work

    def get_antiquarian(self, *args, **kwargs):
        # look for work in the GET or POST parameters
        self.antiquarian = None
        if self.request.method == "GET":
            antiquarian_pk = self.request.GET.get("antiquarian", None)
        elif self.request.method == "POST":
            antiquarian_pk = self.request.POST.get("antiquarian", None)
        if antiquarian_pk:
            try:
                self.antiquarian = Antiquarian.objects.get(pk=antiquarian_pk)
            except Antiquarian.DoesNotExist:
                raise Http404
        return self.antiquarian

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "anonymous_fragment": self.get_anonymous_fragment(),
                "antiquarian": self.get_antiquarian(),
                "work": self.get_work(),
            }
        )
        return context

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values["antiquarian"] = self.get_antiquarian()
        values["work"] = self.get_work()
        return values


class AddAppositumFragmentLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, FormView
):
    check_lock_object = "anonymous_fragment"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = "research/add_appositum_fragment_link.html"

    form_class = AppositumFragmentLinkForm
    permission_required = (
        "research.change_anonymousfragment",
        "research.add_appositumfragmentlink",
    )

    def get_success_url(self, *args, **kwargs):
        if "another" in self.request.POST:
            return self.request.path
        return reverse(
            "anonymous_fragment:detail", kwargs={"pk": self.get_anonymous_fragment().pk}
        )

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, "anonymous_fragment", False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment, pk=self.kwargs.get("pk")
            )
        return self.anonymous_fragment

    def form_valid(self, form):
        data = form.cleaned_data
        fragment = data["linked_to"]
        if fragment:
            fragment.apposita.add(self.anonymous_fragment)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "anonymous_fragment": self.get_anonymous_fragment(),
            }
        )
        return context


@method_decorator(require_POST, name="dispatch")
class RemoveAppositumLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, RedirectView
):
    check_lock_object = "anonymous_fragment"
    permission_required = ("research.change_anonymousfragment",)

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_anonymous_fragment()
        return super().dispatch(request, *args, **kwargs)

    def get_anonymous_fragment(self, *args, **kwargs):
        if not getattr(self, "anonymous_fragment", False):
            self.anonymous_fragment = get_object_or_404(
                AnonymousFragment, pk=self.kwargs.get("pk")
            )
        return self.anonymous_fragment

    def get_success_url(self, *args, **kwargs):
        return reverse(
            "anonymous_fragment:detail", kwargs={"pk": self.anonymous_fragment.pk}
        )

    def get_appositum_link(self, *args, **kwargs):
        if not getattr(self, "link", False):
            self.link = get_object_or_404(
                AppositumFragmentLink, pk=self.kwargs.get("link_pk")
            )
        return self.link

    def post(self, request, *args, **kwargs):
        anonymous_fragment = self.get_anonymous_fragment()
        link = self.get_appositum_link()
        if not link.linked_to:
            link.delete()
        else:
            # if linked to a fragment remove it this way
            link.linked_to.apposita.remove(anonymous_fragment)
        return redirect(self.get_success_url())


class FragmentDetailView(
    CanLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView
):
    model = Fragment
    permission_required = ("research.view_fragment",)

    def get_context_data(self, **kwargs):
        fragment = self.get_object()
        context = super().get_context_data(**kwargs)

        context["inline_update_url"] = "fragment:update_fragment_link"
        context["all_antiquarians"] = [
            {
                "antiquarian": link.antiquarian,
                "definite_antiquarian": link.definite_antiquarian,
            }
            for link in fragment.get_all_links()
        ]
        # TODO: still need to make ant list distinct
        return context


class AnonymousFragmentDetailView(FragmentDetailView):
    model = AnonymousFragment
    permission_required = ("research.view_fragment",)


@method_decorator(require_POST, name="dispatch")
class FragmentDeleteView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    model = Fragment
    success_url = reverse_lazy("fragment:list")
    permission_required = ("research.delete_fragment",)


@method_decorator(require_POST, name="dispatch")
class AnonymousFragmentDeleteView(FragmentDeleteView):
    model = AnonymousFragment
    success_url = reverse_lazy("anonymous_fragment:list")
    permission_required = ("research.delete_fragment",)


class FragmentUpdateView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    model = Fragment
    form_class = FragmentForm
    permission_required = ("research.change_fragment",)

    def get_success_url(self, *args, **kwargs):
        return reverse("fragment:detail", kwargs={"pk": self.object.pk})


class AnonymousFragmentUpdateView(FragmentUpdateView):
    model = AnonymousFragment
    form_class = AnonymousFragmentForm
    permission_required = ("research.change_fragment",)

    def get_success_url(self, *args, **kwargs):
        return reverse("anonymous_fragment:detail", kwargs={"pk": self.object.pk})


@method_decorator(require_POST, name="dispatch")
class AnonymousFragmentConvertToFragmentView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, View
):
    model = AnonymousFragment
    permission_required = "research.change_anonymousfragment"

    def get_queryset(self):
        return self.model._default_manager.all()

    def get_object(self):
        pk = self.kwargs.get("pk")
        queryset = self.get_queryset()
        if pk is None:
            raise AttributeError(
                f"{self.__class__.__name__} must be called with a pk in the URLconf."
            )
        else:
            queryset = queryset.filter(pk=pk)
        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(
                f"No {queryset.model._meta.verbose_name}s found matching the query"
            )
        return obj

    def post(self, request, *args, **kwargs):
        print("running post")
        fragment = convert_anonymous_fragment_to_fragment(self.get_object())
        success_url = reverse("fragment:detail", kwargs={"pk": fragment.pk})
        return HttpResponseRedirect(success_url)


@method_decorator(require_POST, name="dispatch")
class UnlinkedFragmentConvertToAnonymousView(AnonymousFragmentConvertToFragmentView):
    model = Fragment
    permission_required = "research.change_fragment"

    def post(self, request, *args, **kwargs):
        fragment = self.get_object()
        if fragment.is_unlinked:
            anonymous_fragment = convert_unlinked_fragment_to_anonymous_fragment(
                self.get_object()
            )
            success_url = reverse(
                "anonymous_fragment:detail", kwargs={"pk": anonymous_fragment.pk}
            )
            return HttpResponseRedirect(success_url)
        else:
            return HttpResponseBadRequest()


class FragmentUpdateAntiquariansView(FragmentUpdateView):
    model = Fragment
    form_class = FragmentAntiquariansForm
    permission_required = ("research.change_fragment",)
    # use a different template showing fewer fields
    template_name = "research/fragment_antiquarians_form.html"


class FragmentUpdateCommentaryView(FragmentUpdateView):
    model = Fragment
    form_class = FragmentCommentaryForm
    permission_required = ("research.change_fragment",)
    template_name = "research/fragment_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "editing": "commentary",
            }
        )
        return context


class AnonymousFragmentUpdateCommentaryView(AnonymousFragmentUpdateView):
    model = AnonymousFragment
    form_class = AnonymousFragmentCommentaryForm
    permission_required = ("research.change_fragment",)
    template_name = "research/anonymousfragment_detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "editing": "commentary",
            }
        )
        return context


class FragmentAddWorkLinkView(
    CheckLockMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GetWorkLinkRequestDataMixin,
    FormView,
):
    check_lock_object = "fragment"

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_fragment()
        return super().dispatch(request, *args, **kwargs)

    template_name = "research/add_work_link.html"
    form_class = FragmentLinkWorkForm
    permission_required = (
        "research.change_fragment",
        "research.add_fragmentlink",
    )
    is_update = False

    def get_success_url(self, *args, **kwargs):
        if "another" in self.request.POST:
            return self.request.path

        return reverse("fragment:detail", kwargs={"pk": self.get_fragment().pk})

    def get_fragment(self, *args, **kwargs):
        if not getattr(self, "fragment", False):
            self.fragment = get_object_or_404(Fragment, pk=self.kwargs.get("pk"))
        return self.fragment

    def form_valid(self, form):
        data = form.cleaned_data
        antiquarian = data["antiquarian"]

        data["fragment"] = self.get_fragment()
        data["antiquarian"] = antiquarian
        FragmentLink.objects.get_or_create(**data)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "fragment": self.get_fragment(),
                "work": self.get_work(),
                "antiquarian": self.get_antiquarian(),
                "definite_antiquarian": self.get_definite_antiquarian(),
                "definite_work": self.get_definite_work(),
            }
        )
        return context


@method_decorator(require_POST, name="dispatch")
class RemoveFragmentLinkView(
    CheckLockMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    # TODO:update so if removing work/book, they become unknown; antiquarian link stays
    check_lock_object = "fragment"
    model = FragmentLink

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_fragment()
        # self.reassign_to_unknown()
        return super().dispatch(request, *args, **kwargs)

    # base class for both remove work and remove book from a fragment
    permission_required = ("research.change_fragment",)

    def get_success_url(self, *args, **kwargs):
        return self.request.META.get(
            "HTTP_REFERER", reverse("fragment:detail", kwargs={"pk": self.fragment.pk})
        )

    def get_fragment(self, *args, **kwargs):
        if not getattr(self, "fragment", False):
            self.fragment = self.get_object().fragment
        return self.fragment

    def reassign_to_unknown(self, *args, **kwargs):
        # if book in request...?
        self.book = self.work.unknown_book
        # if work in request...?
        self.work = self.antiquarian.unknown_work


class FragmentUpdateWorkLinkView(
    CheckLockMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    GetWorkLinkRequestDataMixin,
    UpdateView,
):
    check_lock_object = "fragment"
    model = FragmentLink
    template_name = "research/partials/render_inline_worklink_form.html"
    form_class = FragmentLinkWorkForm
    is_update = True
    permission_required = "research.change_fragment"

    def get_fragment(self, *args, **kwargs):
        if not getattr(self, "fragment", False):
            self.fragment = self.get_object().fragment
        return self.fragment

    def dispatch(self, request, *args, **kwargs):
        # need to ensure we have the lock object view attribute
        # initialised in dispatch
        self.get_fragment()
        self.get_initial()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial["work"] = self.get_object().work
        initial["antiquarian"] = self.get_object().antiquarian
        initial["book"] = self.get_object().book
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        self.object = self.get_object()

        self.object.definite_antiquarian = data["definite_antiquarian"]
        self.object.definite_work = data["definite_work"]
        self.object.definite_book = data["definite_book"]
        self.object.book = data["book"]

        self.object.save()

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "link": self.object,
                "inline_update_url": "fragment:update_fragment_link",
                "definite_antiquarian": self.get_definite_antiquarian(),
                "definite_work": self.get_definite_work(),
                "can_edit": True,
                "has_object_lock": True,
            }
        )
        return context

    def get_success_url(self, *args, **kwargs):
        return self.request.META.get(
            "HTTP_REFERER", reverse("fragment:detail", kwargs={"pk": self.fragment.pk})
        )

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        self.object.save()
        context = self.get_context_data()

        return render(request, "research/partials/linked_work.html", context)


class MoveAnonymousTopicLinkView(LoginRequiredMixin, View):
    render_partial_template = "research/partials/ordered_anonymoustopiclink_area.html"

    def render_valid_response(self, topic_id):
        view = AnonymousFragmentListView()
        topic = Topic.objects.get(id=topic_id)
        qs = view.get_queryset(topic=topic)
        context = {
            "object_list": qs,
            "has_object_lock": True,
            "can_edit": True,
            "perms": PermWrapper(self.request.user),
        }
        html = render_to_string(self.render_partial_template, context)
        ajax_data = {"status": 200, "html": html}
        return JsonResponse(data=ajax_data, safe=False)

    def post(self, *args, **kwargs):
        anonymoustopiclink_pk = self.request.POST.get("anonymoustopiclink_id", None)
        topic_id = self.request.POST.get("topic_id", None)
        if anonymoustopiclink_pk and topic_id:
            # moving an anonymous topic link in the collection
            try:
                anonymoustopiclink = AnonymousTopicLink.objects.get(
                    pk=anonymoustopiclink_pk
                )

                if anonymoustopiclink.fragment.get_all_links().count() > 0:
                    raise BadRequest("Apposita cannot be reordered within a topic")

                if "move_to" in self.request.POST:
                    pos = int(self.request.POST.get("move_to"))
                    anonymoustopiclink.move_to(pos)

                return self.render_valid_response(topic_id)

            except (Topic.DoesNotExist, AnonymousTopicLink.DoesNotExist, KeyError):
                raise Http404

        raise Http404
