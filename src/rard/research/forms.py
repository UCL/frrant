from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from rard.research.models import (AnonymousFragment, Antiquarian, Book,
                                  CitingAuthor, CitingWork, Comment, Fragment,
                                  OriginalText, Testimonium, Work)
from rard.research.models.base import (AppositumFragmentLink, FragmentLink,
                                       TestimoniumLink)


class AntiquarianIntroductionForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ('name',)  # need to specify at least one field

    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Introduction',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.introduction:
            self.instance.introduction.update_content_mentions()
            self.fields['introduction_text'].initial = \
                self.instance.introduction.content
        self.fields['name'].required = False

    def save(self, commit=True):
        if commit:
            instance = super().save(commit=False)  # no need to save owner
            # introduction will have been created at this point
            instance.introduction.content = \
                self.cleaned_data['introduction_text']
            instance.introduction.save()
        return instance


class AntiquarianDetailsForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ('name', 'order_name', 're_code', 'date_range', 'order_year',)
        labels = {'order_name': 'Name for alphabetisation'}


class AntiquarianCreateForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ('name', 'order_name', 're_code', 'date_range', 'order_year',)
        labels = {'order_name': 'Name for alphabetisation'}

    introduction_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Introduction',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.introduction:
            self.fields['introduction_text'].initial = \
                self.instance.introduction.content

    def save(self, commit=True):
        instance = super().save(commit)
        if commit:
            instance.save_without_historical_record()
            # introduction will have been created at this point
            instance.introduction.content = \
                self.cleaned_data['introduction_text']
            instance.introduction.save_without_historical_record()
        return instance


class AntiquarianUpdateWorksForm(forms.ModelForm):

    class Meta:
        model = Antiquarian
        fields = ('works',)
        widgets = {
          'works': forms.CheckboxSelectMultiple,
        }


class BookWidget(forms.MultiWidget):
    template_name = 'widgets/book.html'

    def __init__(self, *args, **kwargs):
        super(BookWidget, self).__init__(
            widgets = (
                forms.widgets.NumberInput(attrs={
                    'placeholder': 'Number',
                }),
                forms.widgets.TextInput(attrs={
                    'placeholder': 'Book title',
                }),
            ),
            *args, **kwargs
        )

    def decompress(self, value):
        return value or [None, None]


class BookField(forms.MultiValueField):
    widget = BookWidget

    def __init__(self, *args, **kwargs):
        super(BookField, self).__init__(
            fields = (
                forms.IntegerField(required=False, min_value=1),
                forms.CharField(required=False, max_length=128),
            ),
            require_all_fields=False,
            *args,
            **kwargs
        )

    def validate(self, value):
        super().validate(value)
        if value[0] or value[1]:
            if not value[0]:
                raise forms.ValidationError(
                    _("Book '%(title)s' needs a number"),
                    params={'title': value[1]},
                    code='book-number-needed'
                )
            if not value[1]:
                raise forms.ValidationError(
                    _('Book number %(number)d needs a title'),
                    params={'number': value[0]},
                    code='book-title-needed'
                )

    def compress(self, data):
        return data


class BooksWidget(forms.MultiWidget):
    template_name = 'widgets/books.html'

    def __init__(self, count, *args, **kwargs):
        self.count = count
        super(BooksWidget, self).__init__(
            widgets=[BookWidget] * count,
            *args, **kwargs
        )

    def decompress(self, value):
        return value or [None] * self.count


class BooksField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        try:
            count = kwargs['widget'].count
        except:
            count = 5
        super(BooksField, self).__init__(
            fields=[BookField(required=False) for n in range(0, count)],
            require_all_fields=False,
            *args,
            **kwargs
        )

    def compress(self, data):
        return data

    def validate(self, value):
        super().validate(value)
        seen = {}
        dups = {}
        for v in value:
            if v:
                n = v[0]
                if n in seen:
                    dups[n] = True
                else:
                    seen[n] = True
        if dups:
            raise forms.ValidationError(
                _('The following book numbers are duplicated, please make them all distinct: %(nos)s'),
                params={'nos': ', '.join(map(str, dups.keys()))},
                code='book-number-duplicated'
            )


class WorkForm(forms.ModelForm):

    antiquarians = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Antiquarian.objects.all(),
        required=False,
    )

    books = BooksField(widget=BooksWidget(8))

    class Meta:
        model = Work
        fields = (
            'name',
            'subtitle',
            'antiquarians',
            'number_of_books',
            'date_range',
            'order_year',
            'books',
        )
        labels = {'name': 'Name of Work'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # if we are editing an existing work then init the antiquarian set
        # on the form
        if self.instance and self.instance.pk:
            self.fields['antiquarians'].initial = \
                self.instance.antiquarian_set.all()


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        exclude = ('work',)

    def clean(self):
        cleaned_data = super().clean()
        number = self.cleaned_data.get('number', None)
        subtitle = self.cleaned_data.get('subtitle', None)
        if not (number or subtitle):
            ERR = _('Please give a number or a subtitle.')
            self.add_error('number', ERR)
            self.add_error('subtitle', ERR)
        return cleaned_data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        labels = {'content': _('Add Comment')}
        widgets = {
          'content': forms.Textarea(attrs={'rows': 3}),
        }


class CitingWorkForm(forms.ModelForm):

    new_citing_work = forms.BooleanField(required=False)
    new_author = forms.BooleanField(required=False)
    new_author_name = forms.CharField(
        required=False,
        label='New Author Name',
    )

    class Meta:
        model = CitingWork
        fields = (
            'new_citing_work',
            'author',
            'new_author',
            'new_author_name',
            'title',
            'edition'
        )
        labels = {
            'author': _('Choose Existing Author'),
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
                    if field_name == 'new_citing_work':
                        self.fields[field_name].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            if self.cleaned_data['new_author']:
                new_author_name = self.cleaned_data['new_author_name']
                author = CitingAuthor.objects.create(name=new_author_name)
                instance.author = author
            instance.save()
        return instance


class OriginalTextForm(forms.ModelForm):

    class Meta:
        model = OriginalText
        fields = ('citing_work', 'reference', 'content', 'apparatus_criticus')
        labels = {
            'content': _('Original Text'),
            'citing_work': _('Choose Existing'),
        }
        widgets = {
          'apparatus_criticus': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # when creating an original text we also offer the option
        # of creating a new citing work. Hence we allow the selection
        # of an existing instance to be blank and assign a newly-created
        # work to the original text instance in the view
        self.set_citing_work_required(True)

    def set_citing_work_required(self, required):
        # to allow set/reset required fields dynically in the view
        self.fields['citing_work'].required = required


class CommentaryFormBase(forms.ModelForm):
    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Commentary',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.commentary:
            self.instance.commentary.update_content_mentions()
            self.fields['commentary_text'].initial = \
                self.instance.commentary.content

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            # commentary will have been created at this point via post_save
            instance.commentary.content = self.cleaned_data['commentary_text']
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


class HistoricalFormBase(forms.ModelForm):

    definite_antiquarians = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Antiquarian.objects.all(),
        required=False,
    )

    possible_antiquarians = forms.ModelMultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        queryset=Antiquarian.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['definite_antiquarians'].initial = \
            self.instance.definite_antiquarians()

        self.fields['possible_antiquarians'].initial = \
            self.instance.possible_antiquarians()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:

            link_classes = {
                Testimonium: TestimoniumLink,
                Fragment: FragmentLink
            }
            link_class = link_classes[self._meta.model]
            instance.save()
            self.save_m2m()

            # create links for the antiquarians and works mentioned
            definite_antiquarians = self.cleaned_data['definite_antiquarians']
            for a in definite_antiquarians.all():
                data = {
                    'antiquarian': a,
                    link_class.linked_field: instance,
                    'definite': True,
                    'work': None
                }
                link_class.objects.get_or_create(**data)

            # clear others
            data = {
                link_class.linked_field: instance,
                'work': None,
                'definite': True
            }
            link_class.objects.filter(**data).exclude(
                antiquarian__in=definite_antiquarians
            ).delete()

            possible_antiquarians = self.cleaned_data['possible_antiquarians']
            for a in possible_antiquarians.all():
                data = {
                    'antiquarian': a,
                    link_class.linked_field: instance,
                    'definite': False,
                    'work': None
                }
                link_class.objects.get_or_create(**data)

            # clear others
            data = {
                link_class.linked_field: instance,
                'definite': False,
                'work': None
            }
            link_class.objects.filter(**data).exclude(
                antiquarian__in=possible_antiquarians
            ).delete()

        return instance


class FragmentAntiquariansForm(HistoricalFormBase):
    class Meta:
        model = Fragment
        fields = ()


class TestimoniumAntiquariansForm(HistoricalFormBase):
    class Meta:
        model = Testimonium
        fields = ()


class FragmentForm(HistoricalFormBase):

    class Meta:
        model = Fragment
        fields = ('topics', 'date_range', 'order_year',)
        widgets = {'topics': forms.CheckboxSelectMultiple}


class AnonymousFragmentForm(forms.ModelForm):

    class Meta:
        model = AnonymousFragment
        fields = ('topics', 'date_range', 'order_year',)
        widgets = {'topics': forms.CheckboxSelectMultiple}


class TestimoniumForm(HistoricalFormBase):

    class Meta:
        model = Testimonium
        fields = ()


class BaseLinkWorkForm(forms.ModelForm):
    class Meta:
        fields = ('work', 'book', 'definite',)
        labels = {'definite': _('Definite Link')}

    def __init__(self, *args, **kwargs):
        work = kwargs.pop('work')

        super().__init__(*args, **kwargs)
        self.fields['book'].required = False
        if work:
            self.fields['work'].initial = work
            self.fields['book'].queryset = work.book_set.all()
        else:
            self.fields['book'].queryset = Book.objects.none()
            self.fields['book'].disabled = True


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
        fields = ('antiquarian', 'work', 'exclusive', 'book',)

    def __init__(self, *args, **kwargs):

        antiquarian = kwargs.pop('antiquarian')
        work = kwargs.pop('work')

        super().__init__(*args, **kwargs)

        self.fields['work'].required = False
        self.fields['book'].required = False
        self.fields['exclusive'].disabled = True

        if antiquarian:
            self.fields['antiquarian'].initial = antiquarian
            self.fields['work'].queryset = antiquarian.works.all()
            self.fields['work'].disabled = False
        else:
            self.fields['work'].queryset = Work.objects.none()
            self.fields['work'].disabled = True

        if work:
            self.fields['work'].initial = work
            self.fields['book'].queryset = work.book_set.all()
            self.fields['exclusive'].disabled = False
        else:
            self.fields['book'].queryset = Book.objects.none()
            self.fields['book'].disabled = True


class AppositumFragmentLinkForm(forms.ModelForm):

    # for linking to antiquarian, work or book
    # mechanism is different for fragment

    class Meta:
        model = AppositumFragmentLink
        fields = ('linked_to',)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['linked_to'].initial = Fragment.objects.all()
