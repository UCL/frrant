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
