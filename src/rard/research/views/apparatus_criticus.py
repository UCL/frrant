import json
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import View

from rard.research.forms import OriginalTextDetailsForm
from rard.research.models import (
    AnonymousFragment,
    ApparatusCriticusItem,
    Fragment,
    OriginalText,
    Testimonium,
)


class ApparatusCriticusLineViewBase(View):
    render_partial_template = "research/partials/apparatus_criticus_builder.html"

    def process_content(self, content_html):
        # Quill wraps paragraphs in <p></p>, which we do not want.
        # remove any final </p>
        m = re.fullmatch(r"(.*)</p>\s*", content_html)
        content = m and m.group(1) or content_html
        # remove all <p>s (this will leave a leading space)
        content = content.replace("<p>", " ")
        # turn all remaining </p>s into \n, and remove leading space
        content = re.sub(r"\s*</p>\s*", "\n", content).strip()
        # Quill sometimes puts <br> onto blank lines; make this always happen
        content = re.sub(r"\n\n", "\n<br>\n", content)
        return content

    def render_valid_response(self, original_text):
        context = {
            "original_text": original_text,
            "form": OriginalTextDetailsForm(instance=original_text),
        }
        html = render_to_string(self.render_partial_template, context)
        ajax_data = {"status": 200, "html": html}
        return JsonResponse(data=ajax_data, safe=False)


@method_decorator(require_POST, name="dispatch")
class CreateApparatusCriticusLineView(
    LoginRequiredMixin, ApparatusCriticusLineViewBase
):
    def post(self, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404

        parent_id = self.request.POST.get("parent_id", None)
        insert_at = self.request.POST.get("insert_at", None)
        content_html = self.request.POST.get("content", None)
        content = self.process_content(content_html)

        if not all((parent_id, insert_at, content)):
            raise Http404

        # moving a topic in the collection
        try:
            original_text = OriginalText.objects.get(pk=parent_id)
            line = original_text.apparatus_criticus_items.create(
                order=int(insert_at), content=content
            )
            line.move_to(int(insert_at))
            return self.render_valid_response(original_text)

        except (OriginalText.DoesNotExist, KeyError):
            raise Http404

        raise Http404


class DeleteApparatusCriticusLineView(
    LoginRequiredMixin, ApparatusCriticusLineViewBase
):
    def post(self, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404

        line_id = self.request.POST.get("line_id", None)

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


class UpdateApparatusCriticusLineView(
    LoginRequiredMixin, ApparatusCriticusLineViewBase
):
    def post(self, *args, **kwargs):
        if not self.request.accepts("application/json"):
            raise Http404
        POST_data = json.loads(self.request.body)
        line_id = POST_data.get("line_id", None)
        content_html = POST_data.get("content", None)

        content = self.process_content(content_html)

        if not all((line_id, content)):
            raise Http404

        # moving a topic in the collection
        try:
            line = ApparatusCriticusItem.objects.get(pk=line_id)
            line.content = content
            line.save()
            return HttpResponse(status=204)

        except (ApparatusCriticusItem.DoesNotExist, KeyError):
            raise Http404

        raise Http404


@method_decorator(require_GET, name="dispatch")
class ApparatusCriticusSearchView(LoginRequiredMixin, View):
    context_object_name = "results"

    def get(self, request, *args, **kwargs):
        if not request.accepts("application/json"):
            raise Http404

        ajax_data = []
        model_name = ApparatusCriticusItem.__name__

        # TODO here check whether we are looking at a parent object,
        # get its letter e.g. F, T or whatever

        def get_index_display(item):
            if self.parent_object:
                # need to include the ordinal of the original text, if relevant
                # (this is decided in the method called below)
                ordinal = (
                    self.original_text.ordinal_with_respect_to_parent_object()
                )  # noqa
                return "%s%s" % (ordinal, str(item.order + 1))
            else:
                return str(item.order + 1)

        # return just the name, pk and type for display
        # iterate the app crit items
        for item in self.get_queryset():
            ajax_data.append(
                {
                    "id": item.pk,
                    "target": model_name,
                    "parent": self.parent_object.pk
                    if self.parent_object
                    else "",  # noqa
                    "originalText": self.original_text.pk,
                    # 'value': str(o),  # to have full name in the text mention
                    # 'value': str(o.order + 1),  # or to just have the number
                    "value": get_index_display(item),
                    "list_display": strip_tags(str(item)),  # what to show in the list
                }
            )

        return JsonResponse(data=ajax_data, safe=False)

    def get_queryset(self):
        def search_original_text_ordinal(s):
            # check whether they entered a letter in the search field
            import string

            if len(s) == 0:
                return None

            c = s[0]
            return c if c in string.ascii_lowercase else None

        def search_term_as_integer(s):
            # we restrict to integers so #1 and #2 etc work
            try:
                # they will possibly have entered #a1 or #f4
                to_search = s
                c = search_original_text_ordinal(to_search)
                if c:
                    to_search = to_search.lstrip(c)
                return int(to_search)
            except ValueError:
                return None

        search_term = self.request.GET.get("q", "")

        pk = self.request.GET.get("object_id", None)
        object_class = self.request.GET.get("object_class", None)

        self.original_text = None

        # if they user entered e.g. #1 or #a1 this should return 1
        app_crit_one_index = search_term_as_integer(search_term)
        ordinal = search_original_text_ordinal(search_term)

        # store any parent object so called knows whether we are we
        # looking at an original text
        # object or is it a parent e.g. a fragment
        self.parent_object = None

        if object_class != "originaltext":
            self.is_parent_model = True

            # if we are editing a parent item that has several original texts
            # then we insist they enter the index of the original text
            # that they want the apparatus criticuses for.
            # For example if there are three, we would expect '#a' to
            # invoke a search for app crit items for original text a etc
            # we can be kind however and remove this requirement if the parent
            # object only has ONE original text

            # get the class of the parent object
            cls_ = {
                "fragment": Fragment,
                "testimonium": Testimonium,
                "anonymousfragment": AnonymousFragment,
            }.get(object_class, None)

            try:
                self.parent_object = cls_.objects.get(pk=pk)
                # get all the original texts for this parent object
                original_texts = [o for o in self.parent_object.original_texts.all()]
                if len(original_texts) == 1:
                    self.original_text = original_texts[0]
                elif ordinal:
                    original_text_index = ord(ordinal) - ord("a")
                    self.original_text = original_texts[original_text_index]

            except (AttributeError, IndexError, cls_.DoesNotExist):
                pass

        else:
            # it is an original text object so query its app crits
            try:
                self.original_text = OriginalText.objects.get(pk=pk)
            except OriginalText.DoesNotExist:
                pass

        if not self.original_text:
            return ApparatusCriticusItem.objects.none()

        qs = ApparatusCriticusItem.objects.none()
        if self.original_text:
            qs = self.original_text.apparatus_criticus_items.order_by("order")
            if app_crit_one_index is not None:
                # they will have entered 1-indexed so subtract
                qs = qs.filter(order=app_crit_one_index - 1)

        return qs


@method_decorator(require_POST, name="dispatch")
class RefreshOriginalTextContentView(LoginRequiredMixin, View):
    # take a chunk of text and refresh any apparatus criticus
    # links within it and return to the client

    def post(self, *args, **kwargs):
        if not self.request.is_ajax():
            raise Http404

        existing_content = self.request.POST.get("content")

        # NB we do not _save_ an original text here, we are
        # just hijacking its formatting methods
        o = OriginalText(content=existing_content)
        o.update_content_mentions(save=False)

        # any changes will have been made to the content of that object
        # so return amended version to the client
        ajax_data = {"status": 200, "html": o.content}
        return JsonResponse(data=ajax_data, safe=False)
