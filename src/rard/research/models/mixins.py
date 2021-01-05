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


# class OrderableMixin(object):

#     def related_queryset(self):
#         # by default sort according to all objects of this class
#         # and this can be overidden in the subclasses in case
#         # you need to order e.g. wrt a particular data member e.g. work
#         return self.__class__.objects.all()

#     def prev(self):
#         return self.related_queryset().filter(order__lt=self.order).last()

#     def next(self):
#         return self.related_queryset().filter(order__gt=self.order).first()

#     def swap(self, replacement):
#         self.order, replacement.order = replacement.order, self.order
#         self.save()
#         replacement.save()

#     def up(self):
#         previous = self.prev()
#         if previous:
#             self.swap(previous)

#     def down(self):
#         next_ = self.next()
#         if next_:
#             self.swap(next_)
