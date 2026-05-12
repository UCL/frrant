import re
import string
import unicodedata

from django.utils.html import strip_tags


def strip_combining(content):
    """Converts the content to their base and combining characters,
    then removes the combining ones and returns a string of the base characters
    """
    normalized = unicodedata.normalize("NFD", content)
    return "".join([char for char in normalized if not unicodedata.combining(char)])


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


# Fold [X,Y] transforms all instances of Y into X before matching
# Folds are applied in the specified order, so we don't need
# 'uul' <- 'vul' if we already have 'u' <- 'v'
rard_folds: list[tuple[str, str]] = [
    ("ast", "a est"),
    ("ost", "o est"),
    ("umst", "um est"),
    ("am", "an"),
    ("ausa", "aussa"),
    ("nn", "bn"),
    ("tt", "bt"),
    ("pp", "bp"),
    ("rr", "br"),
    ("ch", "cch"),
    ("clu", "culu"),
    ("claud", "clod"),
    ("has", "hasce"),
    ("his", "hisce"),
    ("hos", "hosce"),
    ("i", "ii"),
    ("i", "j"),
    ("um", "im"),
    ("lagr", "lagl"),
    ("mb", "nb"),
    ("ll", "nl"),
    ("mm", "nm"),
    ("mp", "np"),
    ("mp", "ndup"),
    ("rr", "nr"),
    ("um", "om"),
    ("u", "v"),
    ("u", "y"),
    ("uu", "w"),
    ("ulc", "ulch"),
    ("uul", "uol"),
    ("ui", "uui"),
    ("uum", "uom"),
    ("x", "xs"),
]


punctuation_re = re.compile(
    f"(&[lg]t;)|[{re.escape(string.punctuation)}£¬]"
)


def fold_latin(content: str) -> str:
    for fold_to, fold_from in rard_folds:
        content = content.replace(fold_from, fold_to)
    return content


def fold_latin_and_remove_punctuation(content: str) -> str:
    return fold_latin(punctuation_re.sub("", content))
