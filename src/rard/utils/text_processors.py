import re
import string
import unicodedata

from django.utils.html import strip_tags


def strip_combining(content):
    """Converts the content to their base and combining characters,
    then removes the combining ones and returns a lowercase string of the base characters
    """
    normalized = unicodedata.normalize("NFD", content)
    return "".join(
        [char for char in normalized if not unicodedata.combining(char)]
    ).casefold()


def make_plain_text(content):
    no_unicode = strip_combining(content)
    no_ufeff = no_unicode.replace("\ufeff", "")  # found around mentions for some reason
    # Add a space between tags so adjacent words aren't merged
    no_tags = strip_tags(no_ufeff.replace("><", "> <"))
    no_html_chars = re.sub(r"&\w+;", " ", no_tags)
    no_punctuation = no_html_chars.translate(str.maketrans("", "", string.punctuation))
    no_lone_numbers = re.sub(r"\s\d{1,2}\s", " ", no_punctuation)  # mentions
    no_excess_space = re.sub(r" +", " ", no_lone_numbers)
    return no_excess_space
