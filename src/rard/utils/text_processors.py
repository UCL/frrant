import re
import string

from django.utils.html import strip_tags


def make_plain_text(content):
    no_ufeff = content.replace("\ufeff", "")  # found around mentions for some reason
    # Add a space between tags so adjacent words aren't merged
    no_tags = strip_tags(no_ufeff.replace("><", "> <"))
    no_html_chars = re.sub(r"&\w+;", " ", no_tags)
    no_punctuation = no_html_chars.translate(str.maketrans("", "", string.punctuation))
    no_lone_numbers = re.sub(r"\s\d{1,2}\s", " ", no_punctuation)  # mentions
    no_excess_space = re.sub(r" +", " ", no_lone_numbers)
    return no_excess_space
