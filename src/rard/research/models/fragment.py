from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save

from rard.utils.basemodel import BaseModel


class Fragment(BaseModel):
    name = models.CharField(max_length=128, blank=False)

    subtitle = models.CharField(max_length=128, blank=False)

    apparatus_criticus = models.TextField(default='', blank=True)

    commentary = models.OneToOneField(
        'CommentableText', on_delete=models.SET_NULL, null=True,
        related_name='commentary_for'
    )

    images = models.ManyToManyField('FragmentImage', blank=True)

    topics = models.ManyToManyField('Topic', blank=True)

    definite_works = models.ManyToManyField(
        'Work', related_name='definite_fragments', blank=True
    )

    possible_works = models.ManyToManyField(
        'Work', related_name='possible_fragments', blank=True
    )

    def __str__(self):
        return self.name


def create_commentary(sender, instance, created, **kwargs):
    if created:
        from rard.research.models import CommentableText
        instance.commentary = CommentableText.objects.create()
        instance.save()


def delete_commentary(sender, instance, **kwargs):
    if instance.commentary:
        instance.commentary.delete()


post_save.connect(create_commentary, sender=Fragment)
post_delete.connect(delete_commentary, sender=Fragment)


class Topic(BaseModel):
    name = models.CharField(max_length=128, blank=False)


class FragmentImage(BaseModel):
    title = models.CharField(max_length=128, blank=False)

    description = models.CharField(max_length=128, blank=True)

    credit = models.CharField(max_length=128, blank=True)

    copyright_status = models.CharField(max_length=128, blank=True)

    name_and_attribution = models.CharField(max_length=128, blank=True)

    public_release = models.BooleanField(default=False)

    upload = models.ImageField(
        upload_to=settings.UPLOAD_FOLDER, blank=False
    )

    def __str__(self):
        return self.title
