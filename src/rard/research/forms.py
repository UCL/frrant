import re

from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.forms import ModelMultipleChoiceField, inlineformset_factory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from rard.research.models import (
    AnonymousFragment,
    Antiquarian,
    BibliographyItem,
    Book,
    CitingAuthor,
    CitingWork,
    Comment,
    Fragment,
    OriginalText,
    PublicCommentaryMentions,
    Reference,
    Testimonium,
    Work,
)
from rard.research.models.base import (
    AppositumFragmentLink,
    FragmentLink,
    TestimoniumLink,
)


def _validate_reference_order(ro):
    # check ref order doesn't have any section longer than 5 characters as well
    # as non-numeric
    for section in ro.split("."):
        if len(section) > 5:
            raise forms.ValidationError(
                "Each reference order section should not be longer than 5 "
                "characters.",
                code="subset-too-long",
            )
    if not ro.replace(".", "").isnumeric():
        raise forms.ValidationError(
            "Reference order must contain only numbers.", code="ro-non-numeric"
        )


class BibliographyModelMultipleChoiceField(ModelMultipleChoiceField):
    CLEANR = re.compile("<.*?>")

    def label_from_instance(self, obj):
        # year is optional, leave it out and take tags out of title, trim if long
        ttl = obj.author_surnames[:30] + ":- " + re.sub(self.CLEANR, "", obj.title)
        return (ttl[:75] + "..") if len(ttl) > 75 else ttl


class IntroductionFormBase(forms.ModelForm):
    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Introduction",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.introduction:
            self.instance.introduction.update_content_mentions()
            self.fields[
                "introduction_text"
            ].initial = self.instance.introduction.content
            self.fields["introduction_text"].widget.attrs[
                "class"
            ] = "enableMentions enableCKEditor"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.introduction.content = self.cleaned_data["introduction_text"]
            instance.introduction.save()
        return instance


class AntiquarianIntroductionForm(IntroductionFormBase):
    class Meta:
        model = Antiquarian
        fields = ()


class AntiquarianDetailsForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = (
            "name",
            "order_name",
            "re_code",
            "date_range",
            "order_year",
        )
        labels = {"order_name": "Name for alphabetisation"}


class AntiquarianLinkBibliographyItemForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ["bibliography_items"]

    bibliography_items = BibliographyModelMultipleChoiceField(
        queryset=BibliographyItem.objects.all(),
        widget=forms.SelectMultiple,
        required=True,
    )

    def clean_bibliography_items(self):
        """Add initial bibliography items so we only add new ones"""
        data = self.cleaned_data["bibliography_items"]
        return data.union(self.instance.bibliography_items.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Init the existing bib item set and exclude these from queryset
        self.fields[
            "bibliography_items"
        ].initial = self.instance.bibliography_items.all()
        self.fields["bibliography_items"].queryset = BibliographyItem.objects.exclude(
            antiquarians=self.instance.pk
        )


class AntiquarianCreateForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = (
            "name",
            "order_name",
            "re_code",
            "date_range",
            "order_year",
        )
        labels = {"order_name": "Name for alphabetisation"}

    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Introduction",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.introduction:
            self.fields[
                "introduction_text"
            ].initial = self.instance.introduction.content

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            instance.save_without_historical_record()
            # introduction will have been created at this point
            instance.introduction.content = self.cleaned_data["introduction_text"]
            instance.introduction.save_without_historical_record()
        return instance


class AntiquarianUpdateWorksForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ("works",)
        widgets = {
            "works": forms.CheckboxSelectMultiple,
        }


class BooksWidget(forms.Widget):
    template_name = "widgets/books.html"

    subfields = {
        "num": "Book number",
        "title": "Subtitle",
        "date": "Date range",
        "order": "Order year",
    }

    def format_value(self, value):
        return value

    def value_from_datadict(self, data, files, name):
        # find all <name>_<n>_<subfield_id> parameters
        r = {}  # dict of <n> to dict with keys matching subfields
        for k, v in data.items():
            ps = k.rsplit("_", 2)
            if 2 < len(ps) and ps[0] == name and ps[2] in self.subfields and v:
                i = int(ps[1])
                if i not in r:
                    r[i] = {}
                r[i][ps[2]] = v
        rkeys = list(r.keys())
        # ensure we report the values in the order in which
        # they were input
        rkeys.sort()
        ra = [r[k] for k in rkeys]
        return ra

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx["widget"]["subfields"] = self.subfields
        return ctx


class BooksField(forms.Field):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate(self, value):
        pass

    @staticmethod
    def get_values(value, key):
        return [v[key].strip() for v in value if type(v) is dict and key in v]

    @staticmethod
    def is_integer(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @staticmethod
    def has_numberless_titleless_book(value):
        for v in value:
            if "num" not in v and "title" not in v:
                return True
        return False

    def clean(self, value):
        super().validate(value)
        errors = [
            forms.ValidationError(
                _("Order year %(o)s is not a number"),
                params={"o": o},
                code="book-order-not-a-number",
            )
            for o in self.get_values(value, "order")
            if not self.is_integer(o)
        ]
        nums = []
        non_nums = []
        for v in self.get_values(value, "num"):
            if v:
                if v.isnumeric() and 0 < int(v):
                    nums.append(v)
                else:
                    non_nums.append(v)
        errors += [
            forms.ValidationError(
                _("Book number %(nn)s is not a positive number"),
                params={"nn": nn},
                code="book-number-not-a-number",
            )
            for nn in non_nums
        ]
        seen = {}
        dups = {}
        for n in nums:
            if n in seen:
                dups[n] = True
            else:
                seen[n] = True
        errors += [
            forms.ValidationError(
                _("Book number %(n)s is duplicated."),
                params={"n": dup},
                code="book-number-duplicated",
            )
            for dup in dups.keys()
        ]
        if self.has_numberless_titleless_book(value):
            errors.append(
                forms.ValidationError(
                    _("Books require either a title or a number"),
                    code="numberless-titleless-book",
                )
            )
        if errors:
            raise forms.ValidationError(errors)
        return value


class WorkForm(forms.ModelForm):
    antiquarians = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Antiquarian.objects.all(),
        required=False,
    )

    books = BooksField(widget=BooksWidget, required=False)

    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Introduction",
    )

    class Meta:
        model = Work
        fields = (
            "name",
            "subtitle",
            "antiquarians",
            "number_of_books",
            "date_range",
            "order_year",
            "books",
            "introduction_text",
        )
        labels = {"name": "Name of Work"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if we are editing an existing work then init the antiquarian set
        # on the form
        if self.instance and self.instance.pk:
            self.fields["antiquarians"].initial = self.instance.antiquarian_set.all()

        if self.instance.introduction:
            self.fields[
                "introduction_text"
            ].initial = self.instance.introduction.content
        else:
            self.fields["introduction_text"].attrs = {
                "placeholder": "introduction for work"
            }

    def clean(self):
        cleaned_data = super().clean()
        if "books" in cleaned_data:
            existing_book_numbers = [
                str(b.number) for b in self.instance.book_set.all()
            ]
            new_book_numbers = [
                b["num"] for b in cleaned_data.get("books") if "num" in b
            ]
            overlaps = set(existing_book_numbers) & set(new_book_numbers)
            if overlaps:
                raise forms.ValidationError(
                    [
                        forms.ValidationError(
                            _("There is already a book with number %(n)s"),
                            params={"n": o},
                            code="book-number-already-exists",
                        )
                        for o in overlaps
                    ]
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            instance.save_without_historical_record()
            # introduction will have been created at this point
            instance.introduction.content = self.cleaned_data["introduction_text"]
            instance.introduction.save_without_historical_record()
        return instance


class BookForm(forms.ModelForm):
    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Introduction",
    )

    class Meta:
        model = Book
        fields = (
            "order_year",
            "date_range",
            "order",
            "number",
            "subtitle",
            "introduction_text",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.introduction:
            self.fields[
                "introduction_text"
            ].initial = self.instance.introduction.content
        else:
            self.fields["introduction_text"].attrs = {
                "placeholder": "introduction for book"
            }

    def clean(self):
        cleaned_data = super().clean()
        number = self.cleaned_data.get("number", None)
        subtitle = self.cleaned_data.get("subtitle", None)
        if not (number or subtitle):
            ERR = _("Please give a number or a subtitle.")
            self.add_error("number", ERR)
            self.add_error("subtitle", ERR)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            instance.save_without_historical_record()
            # introduction will have been created at this point
            instance.introduction.content = self.cleaned_data["introduction_text"]
            instance.introduction.save_without_historical_record()
        return instance


class WorkIntroductionForm(IntroductionFormBase):
    class Meta:
        model = Work
        fields = ()


class BookIntroductionForm(IntroductionFormBase):
    class Meta:
        model = Book
        fields = ()


class CommentForm(forms.ModelForm):
    # todo: delete this; not used
    class Meta:
        model = Comment
        fields = ("content",)
        labels = {"content": _("Add Comment")}
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }


class CitingWorkForm(forms.ModelForm):
    new_citing_work = forms.BooleanField(required=False)
    new_author = forms.BooleanField(required=False)
    new_author_name = forms.CharField(
        required=False,
        label="New Author Name",
    )

    class Meta:
        model = CitingWork
        fields = (
            "new_citing_work",
            "author",
            "new_author",
            "new_author_name",
            "title",
            "edition",
        )
        labels = {
            "author": _("Choose Existing Author"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # this form is initially optional as the user might instead choose
        # and existing citing work from a separate form
        self.set_required(False)

    def set_required(self, required):
        # to allow set/reset required fields dynically in the view
        if not required:
            for field_name in self.fields:
                self.fields[field_name].required = required
        else:
            # set the form fields to the required status of
            # of whether required in the model definition (i.e. some fields
            # are optional even if we require the form is filled in)
            for field_name in self.fields:
                try:
                    model_field = self._meta.model._meta.get_field(field_name)
                    self.fields[field_name].required = not model_field.blank
                except FieldDoesNotExist:
                    # not a field in the model so set it to required
                    if field_name == "new_citing_work":
                        self.fields[field_name].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            if self.cleaned_data["new_author"]:
                new_author_name = self.cleaned_data["new_author_name"]
                author = CitingAuthor.objects.create(name=new_author_name)
                instance.author = author
            instance.save()
        return instance


class OriginalTextAuthorForm(forms.ModelForm):
    citing_author = forms.ModelChoiceField(
        queryset=CitingAuthor.objects.all().distinct(),
        required=True,
    )

    class Meta:
        model = OriginalText
        fields = ("citing_work",)

    def __init__(self, *args, **kwargs):
        # if we have a citing author selected then populate the works
        # field accordingly. NB this pop needs to be done before calling
        # the super class
        author = kwargs.pop("citing_author")
        work = kwargs.pop("citing_work")

        super().__init__(*args, **kwargs)

        self.fields["citing_work"].required = True
        if author:
            self.fields["citing_author"].initial = author
            self.fields["citing_work"].queryset = author.citingwork_set.all()
            if work:
                self.fields["citing_work"].initial = work
        else:
            self.fields["citing_work"].queryset = CitingWork.objects.none()
            self.fields["citing_work"].disabled = True


class OriginalTextDetailsForm(forms.ModelForm):
    new_apparatus_criticus_line = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Add apparatus criticus line",
    )

    reference_order = forms.CharField(validators=[_validate_reference_order])

    class Meta:
        model = OriginalText
        fields = ("content", "apparatus_criticus_blank", "reference_order")
        labels = {
            "content": _("Original Text"),
        }

    def __init__(self, *args, **kwargs):
        original_text = kwargs.get("instance", None)
        if original_text and original_text.pk:
            original_text.update_content_mentions()

        if original_text and original_text.reference_order:
            original_text.reference_order = (
                original_text.remove_reference_order_padding()
            )

        super().__init__(*args, **kwargs)

        if original_text:
            self.fields["content"].widget.attrs["data-object"] = original_text.pk
            # Only enable apparatus criticus editing if object exists
            self.fields["content"].widget.attrs[
                "class"
            ] = "enableApparatusCriticus enableCKEditor"

    def clean_reference_order(self):
        # Reference order needs to be stored as a string with leading 0s such
        # as 00001.00020.02340 for 1.20.2340
        ro = self.cleaned_data["reference_order"]
        return ".".join([i.zfill(5) for i in ro.split(".")])

    def clean(self):
        cleaned_data = super().clean()
        # Should be false if there are any apparatus criticus lines
        app_crit_blank = cleaned_data.get("apparatus_criticus_blank")
        app_crit_lines = self.instance.apparatus_criticus_lines()
        if app_crit_blank and app_crit_lines:
            raise forms.ValidationError(
                {
                    "apparatus_criticus_blank": "Apparatus criticus lines exist for "
                    "this original text so it cannot be left intentionally blank."
                }
            )


class OriginalTextForm(OriginalTextAuthorForm):
    new_apparatus_criticus_line = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Add apparatus criticus line",
    )

    reference_order = forms.CharField(validators=[_validate_reference_order])

    class Meta:
        model = OriginalText
        fields = (
            "citing_work",
            "content",
            "apparatus_criticus_blank",
            "reference_order",
        )
        labels = {
            "content": _("Original Text"),
        }

    def __init__(self, *args, **kwargs):
        original_text = kwargs.get("instance", None)
        if original_text and original_text.pk:
            original_text.update_content_mentions()

        if original_text and original_text.reference_order:
            original_text.reference_order = (
                original_text.remove_reference_order_padding()
            )
        self.fields["content"].widget.attrs[
            "class"
        ] = "enableApparatusCriticus enableCKEditor"

        super().__init__(*args, **kwargs)
        # when creating an original text we also offer the option
        # of creating a new citing work. Hence we allow the selection
        # of an existing instance to be blank and assign a newly-created
        # work to the original text instance in the view
        self.set_citing_work_required(True)

    def set_citing_work_required(self, required):
        # to allow set/reset required fields dynically in the view
        self.fields["citing_work"].required = required

    def clean_reference_order(self):
        # Reference order needs to be stored as a string with leading 0s such
        # as 00001.00020.02340 for 1.20.2340
        ro = self.cleaned_data["reference_order"]
        return ".".join([i.zfill(5) for i in ro.split(".")])


class CommentaryFormBase(forms.ModelForm):
    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Commentary",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.commentary:
            self.instance.commentary.update_content_mentions()
            self.fields["commentary_text"].initial = self.instance.commentary.content
            self.fields["commentary_text"].widget.attrs[
                "class"
            ] = "enableMentions enableFootnotes enableCKEditor"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            # commentary will have been created at this point via post_save
            instance.commentary.content = self.cleaned_data["commentary_text"]
            instance.commentary.save()
        return instance


class FragmentCommentaryForm(CommentaryFormBase):
    class Meta:
        model = Fragment
        fields = ()


class TestimoniumCommentaryForm(CommentaryFormBase):
    class Meta:
        model = Testimonium
        fields = ()


class AnonymousFragmentCommentaryForm(CommentaryFormBase):
    class Meta:
        model = AnonymousFragment
        fields = ()


class PublicCommentaryFormBase(forms.ModelForm):
    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Public Commentary",
    )
    approved = forms.BooleanField(
        label="approved",
        required=False,
        help_text="By approving, you consent to the general public to view this on the final website.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.public_commentary_mentions:
            self.fields[
                "commentary_text"
            ].initial = self.instance.public_commentary_mentions.content
            self.fields[
                "approved"
            ].initial = self.instance.public_commentary_mentions.approved
            self.fields["commentary_text"].widget.attrs["class"] = "enableCKEditor"

    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.public_commentary_mentions:
            pcm = PublicCommentaryMentions.objects.create(
                content=self.cleaned_data["commentary_text"]
            )
            instance.public_commentary_mentions = pcm

        if commit:
            instance.save()
            instance.public_commentary_mentions.content = self.cleaned_data[
                "commentary_text"
            ]
            instance.public_commentary_mentions.approved = self.cleaned_data["approved"]
            instance.public_commentary_mentions.save()
        return instance


class FragmentPublicCommentaryForm(PublicCommentaryFormBase):
    class Meta:
        model = Fragment
        fields = ()


class TestimoniumPublicCommentaryForm(PublicCommentaryFormBase):
    class Meta:
        model = Testimonium
        fields = ()


class AnonymousFragmentPublicCommentaryForm(PublicCommentaryFormBase):
    class Meta:
        model = AnonymousFragment
        fields = ()


class HistoricalFormBase(forms.ModelForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()

        return instance


class FragmentAntiquariansForm(HistoricalFormBase):
    class Meta:
        model = Fragment
        fields = ()


class TestimoniumAntiquariansForm(HistoricalFormBase):
    class Meta:
        model = Testimonium
        fields = ()


class BibliographyItemInlineForm(HistoricalFormBase):
    title = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 1, "class": "enableCKEditor"})
    )

    class Meta:
        model = BibliographyItem
        fields = (
            "authors",
            "author_surnames",
            "year",
            "title",
        )


class BibliographyItemForm(HistoricalFormBase):
    antiquarians = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Antiquarian.objects.all(),
        required=False,
    )

    citing_authors = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=CitingAuthor.objects.all(),
        required=False,
    )

    class Meta:
        model = BibliographyItem
        fields = (
            "authors",
            "author_surnames",
            "year",
            "title",
            "antiquarians",
            "citing_authors",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if editing a bibliography item init the antiquarian and citing_author sets
        if self.instance and self.instance.pk:
            self.fields["antiquarians"].initial = self.instance.antiquarians.all()
            self.fields["citing_authors"].initial = self.instance.citing_authors.all()


class FragmentForm(HistoricalFormBase):
    class Meta:
        model = Fragment
        fields = (
            "topics",
            "date_range",
            "order_year",
        )
        labels = {"date_range": "Chronological reference"}
        widgets = {"topics": forms.CheckboxSelectMultiple}


class AnonymousFragmentForm(forms.ModelForm):
    class Meta:
        model = AnonymousFragment
        fields = (
            "topics",
            "date_range",
            "order_year",
        )
        labels = {"date_range": "Chronological reference"}
        widgets = {"topics": forms.CheckboxSelectMultiple}


class ReferenceForm(forms.ModelForm):
    class Meta:
        model = Reference
        fields = ("editor", "reference_position")


ReferenceFormset = inlineformset_factory(
    OriginalText,
    Reference,
    form=ReferenceForm,
    fields=("editor", "reference_position"),
    labels={"editor": "Editor", "reference_position": "Reference"},
    can_delete=True,
    min_num=1,
    validate_min=True,
    extra=0,
    error_messages={"too_few_forms": "Please add at least one reference"},
)


class TestimoniumForm(HistoricalFormBase):
    class Meta:
        model = Testimonium
        fields = ()


class BaseLinkWorkForm(forms.ModelForm):
    class Meta:
        fields = (
            "antiquarian",
            "work",
            "book",
            "definite_antiquarian",
            "definite_work",
            "definite_book",
        )
        labels = {
            "definite_antiquarian": _("Definite link to Antiquarian"),
            "definite_work": _("Definite link to Work"),
            "definite_book": _("Definite link to Book"),
        }

    def __init__(self, *args, **kwargs):
        # First remove the form kwargs added by GetWorkLinkRequestDataMixin
        update = kwargs.pop("update")
        antiquarian = kwargs.pop("antiquarian")
        work = kwargs.pop("work")
        book = kwargs.pop("book")
        definite_antiquarian = kwargs.pop("definite_antiquarian")
        definite_work = kwargs.pop("definite_work")
        super().__init__(*args, **kwargs)

        # Setup fields
        self.fields["book"].required = False
        self.fields["work"].required = False
        self.fields["definite_antiquarian"] = forms.BooleanField(required=False)
        self.fields["definite_work"] = forms.BooleanField(required=False)
        self.fields["definite_book"] = forms.BooleanField(required=False)

        if update:
            # We don't need empty labels on select widgets if it's an update
            self.fields["antiquarian"].empty_label = None
            self.fields["work"].empty_label = None
            self.fields["book"].empty_label = None

            if "data" in kwargs:
                # Get Work and Book from post data
                if work_id := kwargs["data"]["work"]:
                    work = Work.objects.get(pk=work_id)
                if book_id := kwargs["data"]["book"]:
                    book = Book.objects.get(pk=book_id)
                antiquarian = Antiquarian.objects.get(pk=kwargs["data"]["antiquarian"])
            else:
                # Get everything from initial
                antiquarian = kwargs["initial"]["antiquarian"]
                definite_antiquarian = kwargs["initial"]["definite_antiquarian"]
                work = kwargs["initial"]["work"]
                definite_work = kwargs["initial"]["definite_work"]
                book = kwargs["initial"]["book"]

        if antiquarian:
            self.fields["antiquarian"].initial = antiquarian
            self.fields["work"].queryset = antiquarian.works.all()
            self.fields["definite_antiquarian"].initial = definite_antiquarian
        else:
            self.fields["work"].queryset = Work.objects.none()
            self.fields["work"].disabled = True
            self.fields["definite_work"].widget.attrs["disabled"] = True
            self.fields["book"].disabled = True
            self.fields["definite_book"].widget.attrs["disabled"] = True

        if work:
            self.fields["work"].initial = work
            self.fields["book"].queryset = work.book_set.all()
            self.fields["definite_work"].initial = definite_work
            if work.unknown:
                # Neither work or book can be definite
                self.fields["definite_work"].widget.attrs["disabled"] = True
                self.fields["definite_book"].widget.attrs["disabled"] = True
            self.fields["work"].widget.attrs.update(
                {
                    "hx-get": reverse("work:fetch_books"),
                    "hx-swap": "innerHTML",
                    "hx-trigger": "change",
                    "hx-target": "select#id_book",
                }
            )
        else:
            self.fields["book"].queryset = Book.objects.none()
            self.fields["book"].disabled = True
            self.fields["definite_book"].widget.attrs["disabled"] = True

        if book:
            if book.unknown:
                self.fields["definite_book"].widget.attrs["disabled"] = True

    def clean(self):
        cleaned_data = super().clean()
        work = cleaned_data.get("work")
        if work is None:
            antiquarian = cleaned_data.get("antiquarian")
            work = antiquarian.unknown_work
        book = cleaned_data.get("book")
        if book is None:
            book = work.unknown_book
        definite_work = cleaned_data.get("definite_work")
        definite_book = cleaned_data.get("definite_book")

        if work.unknown and definite_work is True:
            raise forms.ValidationError(
                _("Cannot be definite link to Unknown Work"),
                code="definite-unknown-work",
            )

        if book.unknown and definite_book is True:
            raise forms.ValidationError(
                _("Cannot be definite link to Unknown Book"),
                code="definite-unknown-book",
            )

        if book and not work:
            raise forms.ValidationError(
                _("Work is required for book link."), code="book-without-work"
            )

        return cleaned_data


class FragmentLinkWorkForm(BaseLinkWorkForm):
    class Meta(BaseLinkWorkForm.Meta):
        model = FragmentLink


class TestimoniumLinkWorkForm(BaseLinkWorkForm):
    class Meta(BaseLinkWorkForm.Meta):
        model = TestimoniumLink


class AppositumGeneralLinkForm(forms.ModelForm):
    # for linking to antiquarian, work or book
    # mechanism is different for fragment

    class Meta:
        model = AppositumFragmentLink
        fields = (
            "antiquarian",
            "work",
            "exclusive",
            "book",
        )

    def __init__(self, *args, **kwargs):
        antiquarian = kwargs.pop("antiquarian")
        work = kwargs.pop("work")

        super().__init__(*args, **kwargs)

        self.fields["work"].required = False
        self.fields["book"].required = False
        self.fields["exclusive"].disabled = True

        if antiquarian:
            self.fields["antiquarian"].initial = antiquarian
            self.fields["work"].queryset = antiquarian.works.all()
            self.fields["work"].disabled = False
        else:
            self.fields["work"].queryset = Work.objects.none()
            self.fields["work"].disabled = True

        if work:
            self.fields["work"].initial = work
            self.fields["book"].queryset = work.book_set.all()
            self.fields["exclusive"].disabled = False
        else:
            self.fields["book"].queryset = Book.objects.none()
            self.fields["book"].disabled = True


class AppositumFragmentLinkForm(forms.ModelForm):
    # for linking to antiquarian, work or book
    # mechanism is different for fragment

    class Meta:
        model = AppositumFragmentLink
        fields = ("linked_to",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["linked_to"].widget = forms.Select(
            attrs={
                "id": "search-results",
            },
            choices=[("", "Results will appear here")],
        )


class AppositumAnonymousLinkForm(forms.Form):
    """For linking anonymous fragments as apposita to
    other anonymous fragments"""

    anonymous_fragment = forms.ModelChoiceField(
        queryset=AnonymousFragment.objects.all(), widget=forms.Select()
    )


class CitingWorkCreateForm(forms.ModelForm):
    class Meta:
        model = CitingWork
        fields = (
            "author",
            "title",
            "edition",
            "order_year",
            "date_range",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["author"].queryset = CitingAuthor.objects.exclude(
            order_name=CitingAuthor.ANONYMOUS_ORDERNAME
        )


class CitingAuthorUpdateForm(forms.ModelForm):
    class Meta:
        model = CitingAuthor
        fields = (
            "name",
            "order_name",
            "order_year",
            "date_range",
        )

    bibliography_items = BibliographyModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=BibliographyItem.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields[
                "bibliography_items"
            ].initial = self.instance.bibliography_items.all()
            if self.instance.is_anonymous_citing_author():
                self.fields["order_name"].disabled = True
