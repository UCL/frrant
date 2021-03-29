from django.db.models.signals import post_delete, post_save
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from rard.users.models import User
from rard.utils.basemodel import BaseModel, OrderableModel
from rard.utils.decorators import disable_for_loaddata


class LinkableContentBase(OrderableModel, BaseModel):

    class Meta:
        abstract = True

    # linked object can be left on various object types. First the
    # apparatus criticus but also possibly other things like endnotes
    # so I made this general. Remember to put a generic relation on the
    # parent object class for ease of access to its linked objects.
    # for apparatus criticus items this would be the original text

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()

    parent = GenericForeignKey()

    content = models.TextField(blank=False)

    def __str__(self):
        return self.content


class ApparatusCriticusItem(LinkableContentBase):
    def related_queryset(self):
        # just the items attached to this original text
        return self.parent.apparatus_criticus_lines()

    def __str__(self):
        # display one-indexed list item
        return '%d %s' % (self.order+1, self.content)


@disable_for_loaddata
def handle_add_saved_item(sender, instance, created, **kwargs):
    instance.move_to(instance.order)

@disable_for_loaddata
def handle_deleted_item(sender, instance, **kwargs):
    # when we delete a linkable object we reindex all the rest
    with transaction.atomic():
        qs = instance.related_queryset()
        for count, item in enumerate(qs.all()):
            if item.order != count:
                item.order = count
                item.save()


post_save.connect(handle_add_saved_item, sender=ApparatusCriticusItem)
post_delete.connect(handle_deleted_item, sender=ApparatusCriticusItem)