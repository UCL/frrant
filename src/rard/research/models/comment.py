from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from rard.users.models import User
from rard.utils.basemodel import BaseModel


class Comment(BaseModel):

    class Meta:
        # most recent first
        ordering = ['-created']

    # comments can be left on various object types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    user = models.ForeignKey(
        User, on_delete=models.SET(User.get_sentinel_user)
    )

    content = models.TextField(blank=False)
