from django.db.models.signals import post_delete, post_save


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
    def create_text_object_fields(cls, sender, instance, created, **kwargs):
        if created:
            from rard.research.models.text_object_field import TextObjectField
            for field in cls.get_text_object_fields():
                setattr(instance, field.name, TextObjectField.objects.create())
            instance.save()

    @classmethod
    def delete_text_object_fields(cls, sender, instance, **kwargs):
        for field in cls.get_text_object_fields():
            text_object = getattr(instance, field.name)
            if text_object:
                text_object.delete()

    @classmethod
    def init_text_object_fields(cls):
        post_save.connect(cls.create_text_object_fields, sender=cls)
        post_delete.connect(cls.delete_text_object_fields, sender=cls)
