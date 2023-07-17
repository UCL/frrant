from django.contrib.auth import forms, get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserChangeForm(forms.UserChangeForm):
    class Meta(forms.UserChangeForm.Meta):
        model = User


class UserCreationForm(forms.UserCreationForm):
    error_message = forms.UserCreationForm.error_messages.update(
        {
            "duplicate_username": _("This username has already been taken."),
            "reserved_username": _("This username is reserved."),
            "no_groups": _("Please add the user to at least one group."),
        }
    )

    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields["password1"].required = False
        self.fields["password2"].required = False

    class Meta(forms.UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "groups",
        )

    def clean_username(self):
        username = self.cleaned_data["username"]

        if username == User.SENTINEL_USERNAME:
            raise ValidationError(self.error_messages["reserved_username"])

        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username

        raise ValidationError(self.error_messages["duplicate_username"])

    def clean_groups(self):
        groups = self.cleaned_data["groups"]
        if len(groups) == 0:
            raise ValidationError(self.error_messages["no_groups"])
        return groups
