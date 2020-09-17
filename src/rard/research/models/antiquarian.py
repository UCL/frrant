from django.db import models
from django.db.models.signals import post_delete, post_save

from rard.utils.basemodel import BaseModel


class Antiquarian(BaseModel):
    name = models.CharField(max_length=128, blank=False)

    biography = models.OneToOneField(
        'CommentableText', on_delete=models.SET_NULL, null=True,
        related_name='biography_for'
    )

    re_code = models.CharField(max_length=64, default='', blank=True)

    works = models.ManyToManyField('Work', blank=True)

    def __str__(self):
        return self.name


def create_biography(sender, instance, created, **kwargs):
    if created:
        from rard.research.models import CommentableText
        instance.biography = CommentableText.objects.create()
        instance.save()


def delete_biography(sender, instance, **kwargs):
    if instance.biography:
        instance.biography.delete()


post_save.connect(create_biography, sender=Antiquarian)
post_delete.connect(delete_biography, sender=Antiquarian)
