from django import forms

from rard.research.models import (Antiquarian, CitingWork, Comment, Fragment,
                                  OriginalText, Work)


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
        labels = {'content': 'Add Comment'}
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
        for field_name in self.fields:
            self.fields[field_name].required = required


class OriginalTextForm(forms.ModelForm):
    class Meta:
        model = OriginalText
        fields = ('citing_work', 'reference', 'content', 'apparatus_criticus')
        labels = {'content': 'Original Text'}
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


class FragmentForm(forms.ModelForm):

    commentary_text = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Commentary',
    )
    class Meta:
        model = Fragment
        fields = (
            'name', 'topics',
            'apparatus_criticus',
            'definite_works', 'possible_works',
            'definite_antiquarians', 'possible_antiquarians',
        )
        labels = {'name': 'Fragment Name'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.commentary:
            self.fields['commentary_text'].initial = \
                self.instance.commentary.content

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # commentary will have been created at this point
            instance.commentary.content = self.cleaned_data['commentary_text']
            instance.commentary.save()
            self.save_m2m()
        return instance
