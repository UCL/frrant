from django.db import models

from rard.utils.basemodel import BaseModel


class OriginalText(BaseModel):
    fragment = models.ForeignKey('Fragment', on_delete=models.CASCADE)

    title = models.CharField(max_length=128, blank=False)

    content = models.TextField(blank=False)

    apparatus_criticus = models.TextField(default='', blank=True)


class Concordance(BaseModel):
    original_text = models.ForeignKey('OriginalText', on_delete=models.CASCADE)

    source = models.CharField(max_length=128, blank=False)

    identifier = models.CharField(max_length=128, blank=False)


class Translation(BaseModel):
    original_text = models.ForeignKey('OriginalText', on_delete=models.CASCADE)

    translator_name = models.CharField(max_length=128, blank=False)

    translated_text = models.TextField(blank=False)
