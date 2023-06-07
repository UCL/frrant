from django.db.models.signals import post_delete, post_save
from django.urls import reverse

from rard.utils.decorators import disable_for_loaddata


class TextObjectFieldMixin(object):
    @classmethod
    def get_text_object_fields(cls):
        fields = []
        from rard.research.models.text_object_field import TextObjectField

        for field in cls._meta.fields:
            try:
                if field.related_model.__name__ == TextObjectField.__name__:
                    fields.append(field)
            except AttributeError:
                pass
        return fields

    @classmethod
    @disable_for_loaddata
    def create_text_object_fields(cls, sender, instance, created, **kwargs):
        if created:
            print("textobjectmixin create")
            from rard.research.models.text_object_field import TextObjectField

            for field in cls.get_text_object_fields():
                setattr(instance, field.name, TextObjectField.objects.create())
            instance.save_without_historical_record()

    @classmethod
    @disable_for_loaddata
    def delete_text_object_fields(cls, sender, instance, **kwargs):
        for field in cls.get_text_object_fields():
            text_object = getattr(instance, field.name)
            if text_object:
                text_object.delete()

    @classmethod
    def init_text_object_fields(cls):
        post_save.connect(cls.create_text_object_fields, sender=cls)
        post_delete.connect(cls.delete_text_object_fields, sender=cls)


class HistoryModelMixin(object):
    def related_lock_object(self):  # pragma: no cover
        # the object that needs to have a lock to allow reverts
        class_name = self.__class__.__name__
        raise NotImplementedError(
            "%s must provide a related_lock_object() method" % class_name
        )

    def get_history_title(self):
        return str(self)

    def history_url(self):
        # by default sort according to all objects of this class
        # and this can be overidden in the subclasses in case
        # you need to order e.g. wrt a particular data member e.g. work
        from django.apps import apps

        dd = apps.all_models["research"]
        model_name = next(key for key, value in dd.items() if value == self.__class__)

        try:
            return reverse(
                "history:list", kwargs={"model_name": model_name, "pk": self.pk}
            )
        except NameError:
            return None
