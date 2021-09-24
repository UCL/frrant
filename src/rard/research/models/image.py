from django.conf import settings
from django.db import models

from rard.utils.basemodel import BaseModel


class Image(BaseModel):

    title = models.CharField(max_length=128, blank=False)

    description = models.CharField(max_length=128, blank=True)

    credit = models.CharField(max_length=128, blank=True)

    copyright_status = models.CharField(max_length=128, blank=True)

    name_and_attribution = models.CharField(max_length=128, blank=True)

    public_release = models.BooleanField(default=False)

    upload = models.ImageField(upload_to=settings.UPLOAD_FOLDER, blank=False)

    def __str__(self):
        return self.title
