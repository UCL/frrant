from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Default user for Republican Antiquarians Research Database."""

    email = models.EmailField(_('email address'), unique=True, blank=False)

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)

    def display_name(self):
        return self.name or self.get_full_name() or self.username
