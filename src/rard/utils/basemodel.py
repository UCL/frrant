from django.db import models
from model_utils.models import TimeStampedModel


class BaseModel(TimeStampedModel, models.Model):

    # defines a base model with any required
    # additional common functionality

    class Meta:
        abstract = True
