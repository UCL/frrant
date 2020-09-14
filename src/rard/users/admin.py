from django.conf import settings
from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.utils.crypto import get_random_string

from rard.users.forms import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    DEFAULT_PASSWORD_LENGTH = 12

    form = UserChangeForm
    add_form = UserCreationForm
    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser"
    ]
    search_fields = ['first_name', 'last_name', 'username', 'email']

    add_fieldsets = (
        (None, {
            'fields': (
                'first_name',
                'last_name',
                'username',
                'email',
            ),
        }),
    )

    def save_model(self, request, obj, form, change):
        reset_password = not change and (
            not form.cleaned_data['password1'] or not obj.has_usable_password()
        )
        if reset_password:
            # Django's PasswordResetForm won't let the user reset an unusable
            # password so set it to something random
            obj.set_password(get_random_string(self.DEFAULT_PASSWORD_LENGTH))

        super().save_model(request, obj, form, change)

        if reset_password:
            # the email templates
            subject_template = \
                'registration/account_creation_email_subject.txt'
            email_template = 'registration/account_creation_email.html'
            reset_form = PasswordResetForm({'email': obj.email})
            if reset_form.is_valid():
                reset_form.save(
                    request=request,
                    use_https=request.is_secure(),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    subject_template_name=subject_template,
                    email_template_name=email_template,
                )
