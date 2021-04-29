from django import template

register = template.Library()

@register.filter
def entity_escape(item):
    """
    If you want to put HTML into an attributes value in a template
    (surrounded by single quotes) you are going to need any
    single quotes turned into entities and any entities (including
    those single quotes) escaped as well. This enables HTML to
    be entered into the data-content attribute of a field that
    QuillJS will be rendering.
    """
    s = item.replace("'", "&apos;")
    return s.replace("&", "&amp;")
