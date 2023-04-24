from datetime import timedelta

from django.utils import timezone


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
