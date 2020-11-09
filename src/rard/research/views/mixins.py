from datetime import timedelta

from django.utils import timezone


class DateOrderMixin():
    # orders a queryset by date information
    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.GET.get('order') == 'earliest':
            qs = qs.order_by('year1', 'year2')
        if self.request.GET.get('order') == 'latest':
            qs = qs.order_by('-year1', '-year2')
        return qs

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context.update({
            'order': self.request.GET.get('order'),
        })
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
                request, 'research/user_has_no_lock.html', {'object': editing}
            )

        return super().dispatch(request, *args, **kwargs)


class CanLockMixin:

    def dispatch(self, request, *args, **kwargs):
        from django.shortcuts import redirect
        if request.method == 'POST':
            viewing = self.get_object()
            if ('lock' in request.POST or 'days' in request.POST):
                lock_until = None

                if 'days' in request.POST:
                    days = int(request.POST.get('days'))
                    lock_until = timezone.now() + timedelta(days=days)

                if viewing.is_locked():
                    from django.shortcuts import render
                    return render(
                        request,
                        'research/user_has_no_lock.html',
                        {'object': viewing}
                    )
                viewing.lock(request.user, lock_until)
                return redirect(request.path)

            elif 'unlock' in request.POST:
                if viewing.locked_by == request.user:
                    viewing.unlock()
                    return redirect(request.path)

            elif 'request' in request.POST:
                # we send a request for the item to the person who has lock
                viewing.request_lock(request.user)
                return redirect(request.path)
            elif 'break' in request.POST and request.user.can_break_locks:
                viewing.break_lock(request.user)
                return redirect(request.path)

        return super().dispatch(request, *args, **kwargs)


class SymbolContextMixin:

    # returns context info for the range of symbols available

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        modifiers = [(x, 'Character %s' % x) for x in [
            'F0C3', 'F0C4', 'F0C5', 'F0C6', 'F0C7', 'F0C8', 'F0C9', 'F0CA',
            'F0CB', 'F0CC', 'F0CD', 'F0CE', 'F0CF',
        ]]
        chars = [(('%04x' % i).upper(),
                  'Character %04x' % i) for i in range(60501, 60581)]
        more_chars = [(('%04x' % i).upper(),
                       'Character %04x' % i) for i in range(63665, 63743)]
        # for i in range(60501, 60581):
        #     chars.append(('%04x' % i).upper())
        character_sets = {
            'Character Set 1': chars,
            'Character Set 2': more_chars,
            'Modifiers': modifiers,
        }
        context['character_sets'] = character_sets

        return context
