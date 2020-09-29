from django.views.generic import TemplateView


class HomeView(TemplateView):
    def get_template_names(self):
        if not self.request.user.is_authenticated:
            return ['pages/front.html']
        else:
            return ['research/home.html']
