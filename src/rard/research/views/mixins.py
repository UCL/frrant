from datetime import timedelta

from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView

from rard.research.models import Antiquarian, Work


class DateOrderMixin:
    # orders a queryset by date information
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.GET.get("order") == "earliest":
            qs = qs.order_by("order_year")
        if self.request.GET.get("order") == "latest":
            qs = qs.order_by("-order_year")
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update(
            {
                "order": self.request.GET.get("order"),
            }
        )
        return context


class CheckLockMixin:
    check_lock_object = None

    def dispatch(self, request, *args, **kwargs):
        if self.check_lock_object:
            editing = getattr(self, self.check_lock_object)
        else:
            editing = self.get_object()

        if editing.locked_by != request.user:
            # if not locked by this exact person then we don't allow it
            from django.shortcuts import render

            return render(
                request, "research/user_has_no_lock.html", {"object": editing}
            )

        return super().dispatch(request, *args, **kwargs)


class CanLockMixin:
    def dispatch(self, request, *args, **kwargs):
        from django.shortcuts import redirect

        if request.method == "POST":
            viewing = self.get_object()
            if "lock" in request.POST or "days" in request.POST:
                lock_until = None

                if "days" in request.POST:
                    days = int(request.POST.get("days"))
                    lock_until = timezone.now() + timedelta(days=days)

                if viewing.is_locked():
                    from django.shortcuts import render

                    return render(
                        request, "research/user_has_no_lock.html", {"object": viewing}
                    )
                viewing.lock(request.user, lock_until)
                return redirect(request.path)

            elif "unlock" in request.POST:
                if viewing.locked_by == request.user:
                    viewing.unlock()
                    return redirect(request.path)

            elif "request" in request.POST:
                # we send a request for the item to the person who has lock
                viewing.request_lock(request.user)
                return redirect(request.path)
            elif "break" in request.POST and request.user.can_break_locks:
                viewing.break_lock(request.user)
                return redirect(request.path)

        return super().dispatch(request, *args, **kwargs)


class GetWorkLinkRequestDataMixin:
    def get_antiquarian(self, *args, **kwargs):
        # look for antiquarian in the GET or POST parameters
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

    def get_definite_antiquarian(self, *args, **kwargs):
        # look for definite_antiquarian in the GET or POST parameters
        if self.request.method == "GET":
            return self.request.GET.get("definite_antiquarian", False)
        elif self.request.method == "POST":
            return self.request.POST.get("definite_antiquarian", False)
        else:
            return False

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

    def get_definite_work(self, *args, **kwargs):
        # look for definite_work in the GET or POST parameters
        if self.request.method == "GET":
            return self.request.GET.get("definite_work", False)
        elif self.request.method == "POST":
            return self.request.POST.get("definite_work", False)
        else:
            return False

    def get_definite_book(self, *args, **kwargs):
        # look for definite_book in the GET or POST parameters
        if self.request.method == "GET":
            return self.request.GET.get("definite_book", False)
        elif self.request.method == "POST":
            return self.request.POST.get("definite_book", False)
        else:
            return False

    def get_form_kwargs(self):
        values = super().get_form_kwargs()
        values["antiquarian"] = self.get_antiquarian()
        values["work"] = self.get_work()
        values["definite_antiquarian"] = self.get_definite_antiquarian()
        values["definite_work"] = self.get_definite_work()
        values["update"] = self.is_update

        return values


class TextObjectFieldViewMixin(DetailView):
    template_name = "research/partials/text_object_preview.html"
    model = None
    hx_trigger = None
    textobject_field = None
    hide_empty = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hide_empty"] = self.hide_empty
        context["object_class"] = self.object._meta.model_name
        if self.textobject_field:
            context["text_object"] = getattr(context["object"], self.textobject_field)
        return context


class TextObjectFieldUpdateMixin(object):
    template_name = "research/inline_forms/introduction_form.html"
    success_template_name = "research/partials/text_object_preview.html"
    hx_trigger = None
    textobject_field = None
    hide_empty = False

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data()
        response = render(
            self.request, template_name=self.success_template_name, context=context
        )
        # Add htmx trigger for client side response to update
        if self.hx_trigger:
            response["HX-Trigger"] = self.hx_trigger
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["hide_empty"] = self.hide_empty
        model_name = self.object._meta.model_name
        context["object_class"] = model_name
        # Horrible hack to deal with anonymous fragment namespace not being the same as model_name
        if model_name == "anonymousfragment":
            model_namespace = "anonymous_fragment"
            url_name = self.textobject_field
        # Another horrible hack to deal with books not having their own namespace
        elif model_name == "book":
            model_namespace = "work"
            url_name = "book_introduction"
        else:
            model_namespace = model_name
            url_name = self.textobject_field
        context["cancel_url"] = reverse(
            f"{model_namespace}:{url_name}", args=[self.object.id]
        )
        if self.textobject_field:
            context["text_object"] = getattr(context["object"], self.textobject_field)
        return context
