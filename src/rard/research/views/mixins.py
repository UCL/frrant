from datetime import timedelta

from django.http import Http404
from django.utils import timezone

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
