from django.db import models

from rard.utils.basemodel import BaseModel


class Work(BaseModel):
    name = models.CharField(max_length=128, blank=False)
    subtitle = models.CharField(max_length=128, blank=False)

    def __str__(self):
        return self.name
