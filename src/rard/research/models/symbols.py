from django.db import models

from rard.utils.basemodel import BaseModel


class SymbolGroup(BaseModel):

    class Meta:
        # alphabetical
        ordering = ['name']

    name = models.CharField(max_length=64, blank=False, unique=True)

    def __str__(self):
        return self.name


class Symbol(BaseModel):

    class Meta:
        # alphabetical
        ordering = ['code']

    # each individual symbol can belong to a group
    group = models.ForeignKey(
        'SymbolGroup', default=None, null=True, on_delete=models.SET_NULL
    )

    name = models.CharField(max_length=64, blank=True)

    # the unicode character code
    code = models.CharField(max_length=16, blank=False, unique=True)

    # TODO optionally have a URL to an image file for
    # custom characters we need to add manually

    def get_display_name(self):
        return self.name or 'Code: %s' % self.code

    def __str__(self):
        return self.get_display_name()
