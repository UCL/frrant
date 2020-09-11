from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from rard.utils.basemodel import BaseModel


class User(AbstractUser, BaseModel):
    """Default user for Republican Antiquarians Research Database."""

    email = models.EmailField(_('email address'), unique=True, blank=False)

    def display_name(self):
        return self.get_full_name() or self.username
