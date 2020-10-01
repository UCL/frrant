from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from rard.research.models import (Antiquarian, CitingWork, Comment, Fragment,
                                  OriginalText, Testimonium, Work)


class AntiquarianForm(forms.ModelForm):
    class Meta:
        model = Antiquarian
        fields = ('name', 're_code')

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

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # biography will have been created at this point
            instance.biography.content = self.cleaned_data['biography_text']
            instance.biography.save()
        return instance


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = '__all__'


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
        # self.fields['citing_work'].required = False
        self.set_citing_work_required(False)

    def set_citing_work_required(self, required):
        # to allow set/reset required fields dynically in the view
        self.fields['citing_work'].required = required


class HistoricalFormBase(forms.ModelForm):

    multiselect_help_string = _(
        'Hold down the \"Control\" key on a PC'
        ' or \"Command\" key on a Mac, to select or deselect'
        ' more than one'
    )
    multiselect_help_fields = ()

    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Commentary',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.commentary:
            self.fields['commentary_text'].initial = \
                self.instance.commentary.content
        for name in self.multiselect_help_fields:
            self.fields[name].help_text = self.multiselect_help_string

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # commentary will have been created at this point via post_save
            instance.commentary.content = self.cleaned_data['commentary_text']
            instance.commentary.save()
            self.save_m2m()
        return instance


class FragmentForm(HistoricalFormBase):

    multiselect_help_fields = (
        'definite_works', 'possible_works', 'topics',
        'definite_antiquarians', 'possible_antiquarians'
    )

    class Meta:
        model = Fragment
        fields = (
            'name', 'topics',
            'definite_works', 'possible_works',
            'definite_antiquarians', 'possible_antiquarians',
        )
        labels = {'name': _('Fragment Name')}


class TestimoniumForm(HistoricalFormBase):

    multiselect_help_fields = (
        'definite_works', 'possible_works',
        'definite_antiquarians', 'possible_antiquarians'
    )

    class Meta:
        model = Testimonium
        fields = (
            'name',
            'definite_works', 'possible_works',
            'definite_antiquarians', 'possible_antiquarians',
        )
        labels = {'name': _('Testimonium Name')}
