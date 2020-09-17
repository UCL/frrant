from django.db import models

from rard.users.models import User
from rard.utils.basemodel import BaseModel


class CommentableText(BaseModel):
    content = models.TextField(default='', blank=True)


class Comment(BaseModel):
    parent = models.ForeignKey('CommentableText', on_delete=models.CASCADE)

    user = models.ForeignKey(
        User, on_delete=models.SET(User.get_sentinel_user)
    )

    content = models.TextField(blank=False)
