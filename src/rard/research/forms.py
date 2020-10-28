from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from rard.research.models import (Antiquarian, Book, CitingWork, Comment, Fragment,
                                  OriginalText, Testimonium, Work, Book)
from rard.research.models.base import FragmentLink, TestimoniumLink


class AntiquarianForm(forms.ModelForm):

    class Meta:
        model = Antiquarian
        fields = ('name', 're_code', 'circa', 'year_type', 'year1', 'year2')
        labels = {
            'year1': '',
            'year2': '',
            'year_type': 'Dates',
        }

    biography_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Biography',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.biography:
            self.fields['biography_text'].initial = \
                self.instance.biography.content
        self.fields['year1'].widget.attrs['placeholder'] = 'Enter Year'
        self.fields['year2'].widget.attrs['placeholder'] = 'Enter Year'

    def clean(self):
        cleaned_data = super().clean()
        year_type = self.cleaned_data.get('year_type', None)
        if year_type:
            to_validate = ('year1', )
            if year_type == Antiquarian.YEAR_RANGE:
                to_validate = ('year1', 'year2')

            for name in to_validate:
                value = self.cleaned_data.get(name)
                try:
                    # test it's an acceptable number
                    int(value)
                except (TypeError, ValueError):
                    self.add_error(name, _('Please enter a whole number.'))

        year1 = self.cleaned_data.get('year1', None)
        year2 = self.cleaned_data.get('year2', None)

        if not year_type:
            cleaned_data['year1'] = None
            cleaned_data['year2'] = None
        elif year_type == Antiquarian.YEAR_RANGE:
            if year1 and year2:
                if int(year1) >= int(year2):
                    self.add_error(
                        'year1', _('The start year must be earlier.'))
                    self.add_error(
                        'year2', _('The end year must be later.'))
        else:
            # force year2 off unless we are a range
            cleaned_data['year2'] = None
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # biography will have been created at this point
            instance.biography.content = self.cleaned_data['biography_text']
            instance.biography.save()
        return instance


class AntiquarianUpdateWorksForm(forms.ModelForm):

    class Meta:
        model = Antiquarian
        fields = ('works',)
        widgets = {
          'works': forms.CheckboxSelectMultiple,
        }


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        exclude = ('fragments',)


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('number', 'subtitle',)

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

    class Meta:
        model = CitingWork
        fields = ('new_citing_work', 'author', 'title', 'edition')

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
                    self.fields[field_name].required = True


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


class HistoricalFormBase(forms.ModelForm):

    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Commentary',
    )

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
        if self.instance.commentary:
            self.fields['commentary_text'].initial = \
                self.instance.commentary.content

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

            # commentary will have been created at this point via post_save
            instance.commentary.content = self.cleaned_data['commentary_text']
            instance.commentary.save()
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


class FragmentForm(HistoricalFormBase):

    class Meta:
        model = Fragment
        fields = ('topics',)
        labels = {'name': _('Fragment Name')}
        widgets = {'topics': forms.CheckboxSelectMultiple}


class TestimoniumForm(HistoricalFormBase):

    class Meta:
        model = Testimonium
        fields = ()
        labels = {'name': _('Testimonium Name')}


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
