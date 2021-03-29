from bs4 import BeautifulSoup

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import View

from rard.research.forms import OriginalTextForm
from rard.research.models import ApparatusCriticusItem, OriginalText


class ApparatusCriticusLineViewBase(View):

    render_partial_template = 'research/partials/apparatus_criticus_builder.html'

    def process_content(self, content_html):
        # cannot stop quill from wrapping things with <p></p> so strip
        # that off here
        soup =  BeautifulSoup(content_html)
        p = soup.find('p')
        content = ''.join([str(x) for x in p.children])
        print('have set content to:')
        print(content)
        return content

    def render_valid_response(self, original_text):
        context = {
            'original_text': original_text,
            'form': OriginalTextForm()
        }
        html = render_to_string(self.render_partial_template, context)
        ajax_data = {'status': 200, 'html': html}
        return JsonResponse(data=ajax_data, safe=False)


@method_decorator(require_POST, name='dispatch')
class CreateApparatusCriticusLineView(LoginRequiredMixin,
                                      ApparatusCriticusLineViewBase):


    def post(self, *args, **kwargs):

        if not self.request.is_ajax():
            raise Http404

        parent_id = self.request.POST.get('parent_id', None)
        insert_at = self.request.POST.get('insert_at', None)
        content_html = self.request.POST.get('content', None)

        content = self.process_content(content_html)

        if not all((parent_id, insert_at, content)):
            raise Http404

        # moving a topic in the collection
        try:
            original_text = OriginalText.objects.get(pk=parent_id)
            line = original_text.apparatus_criticus_items.create(
                order=int(insert_at), content=content
            )
            print('line created with order %s' % line.order)
            line.move_to(int(insert_at))
            print('line posn now %s'  % line.order)
            return self.render_valid_response(original_text)

        except (OriginalText.DoesNotExist, KeyError):
            raise Http404

        raise Http404


class DeleteApparatusCriticusLineView(LoginRequiredMixin,
                                      ApparatusCriticusLineViewBase):

    def post(self, *args, **kwargs):

        if not self.request.is_ajax():
            raise Http404

        line_id = self.request.POST.get('line_id', None)

        if not line_id:
            raise Http404

        # moving a topic in the collection
        try:
            line = ApparatusCriticusItem.objects.get(pk=line_id)
            original_text = line.parent
            line.delete()
            return self.render_valid_response(original_text)

        except (ApparatusCriticusItem.DoesNotExist, KeyError):
            raise Http404

        raise Http404


class UpdateApparatusCriticusLineView(LoginRequiredMixin,
                                      ApparatusCriticusLineViewBase):

    def post(self, *args, **kwargs):

        if not self.request.is_ajax():
            raise Http404

        line_id = self.request.POST.get('line_id', None)
        content_html = self.request.POST.get('content', None)

        content = self.process_content(content_html)
        
        if not all((line_id, content)):
            raise Http404

        # moving a topic in the collection
        try:
            line = ApparatusCriticusItem.objects.get(pk=line_id)
            line.content = content
            line.save()
            return self.render_valid_response(line.parent)

        except (ApparatusCriticusItem.DoesNotExist, KeyError):
            raise Http404

        raise Http404


@method_decorator(require_GET, name='dispatch')
class ApparatusCriticusSearchView(LoginRequiredMixin, View):

    context_object_name = 'results'

    def get(self, request, *args, **kwargs):

        if not request.is_ajax():
            raise Http404

        ajax_data = []
        model_name = ApparatusCriticusItem.__class__.__name__

        # return just the name, pk and type for display
        for o in self.get_queryset():
            ajax_data.append(
                {
                    'id': o.pk,
                    'target': model_name,
                    'value': str(o)
                }
            )

        return JsonResponse(data=ajax_data, safe=False)

    def get_queryset(self):

        def search_term_as_integer(s):
            # we restrict to integers so #1 and #2 etc work
            try: 
                # they will have 
                return int(s)
            except ValueError:
                return None

        keywords = self.request.GET.get('q', '')
        print('keywords %s' % keywords)
        if search_term_as_integer(keywords) is None:
            return ApparatusCriticusItem.objects.none()

        pk = self.request.GET.get('original_text', None)
        try:
            o = OriginalText.objects.get(pk=pk)
            qs = o.apparatus_criticus_items.order_by('order')

            # now filter by the search term
            # exact match to the index (for example #1 will appear first)
            index = search_term_as_integer(keywords)
            if index is not None:
                # they will have entered 1-indexed so subtract
                qs = qs.filter(order=index-1)

            return qs.distinct()

        except OriginalText.DoesNotExist:
            pass
    
        return ApparatusCriticusItem.objects.none()
