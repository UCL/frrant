from django.views.generic import TemplateView


class HomeView(TemplateView):
    def get_template_names(self):
        return ["research/home.html"]
