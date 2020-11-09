from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from rard.utils.basemodel import BaseModel


class User(AbstractUser, BaseModel):
    """Default user for Republican Antiquarians Research Database."""

    email = models.EmailField(_('email address'), unique=True, blank=False)

    can_break_locks = models.BooleanField(
        default=False,
        help_text=_(
            'Designates whether this user can override edit locks '
            'on records, regardless of whether they own them.'
        ),
    )

    def display_name(self):
        return self.get_full_name() or self.username

    SENTINEL_USERNAME = 'deleteduser'

    @classmethod
    def get_sentinel_user(cls):
        # for when users are deleted and we don't want
        # everything they created to go with them
        return User.objects.get_or_create(
            first_name='Deleted',
            last_name='User',
            username=cls.SENTINEL_USERNAME
        )[0]
