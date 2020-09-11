import uuid

from django.db import models


class BaseModel(models.Model):

    # defines a base model with any required
    # additional common functionality

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    class Meta:
        abstract = True

    @property
    def reference(self):
        # a short (truncated) version of the id for display
        return self.pk.hex[:8]
