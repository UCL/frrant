from django.contrib.contenttypes.fields import GenericRelation
from django.urls import reverse
from simple_history.models import HistoricalRecords

from rard.research.models.mixins import HistoryModelMixin
from rard.utils.text_processors import make_plain_text

from .base import HistoricalBaseModel, TestimoniumLink


class Testimonium(HistoryModelMixin, HistoricalBaseModel):
    history = HistoricalRecords(
        excluded_fields=[
            "original_texts",
        ]
    )

    def related_lock_object(self):
        return self

    LINK_TYPE = TestimoniumLink

    original_texts = GenericRelation("OriginalText", related_query_name="testimonia")

    def definite_book_links(self):
        return (
            self.antiquarian_testimoniumlinks.filter(
                definite_book=True,
            )
            .order_by("work", "-book")
            .distinct()
        )

    def possible_book_links(self):
        return (
            self.antiquarian_testimoniumlinks.filter(
                definite_book=False,
            )
            .order_by("work", "-book")
            .distinct()
        )

    def definite_work_links(self):
        return (
            self.antiquarian_testimoniumlinks.filter(
                definite_work=True,
            )
            .order_by("work", "-book")
            .distinct()
        )

    def possible_work_links(self):
        return (
            self.antiquarian_testimoniumlinks.filter(
                definite_work=False,
            )
            .order_by("work", "-book")
            .distinct()
        )

    def definite_antiquarian_links(self):
        return self.antiquarian_testimoniumlinks.filter(definite_antiquarian=True)

    def possible_antiquarian_links(self):
        return self.antiquarian_testimoniumlinks.filter(definite_antiquarian=False)

    def get_absolute_url(self):
        return reverse("testimonium:detail", kwargs={"pk": self.pk})

    def get_all_names(self):
        return [link.get_display_name() for link in self.get_all_links()]

    def get_all_work_names(self):
        # all the names wrt works
        return [link.get_work_display_name() for link in self.get_all_links()]

    def get_all_links(self):
        return (
            TestimoniumLink.objects.filter(testimonium=self)
            .order_by(
                "antiquarian__name",
                "work__worklink__order",
                "book__unknown",
                "book__order",
            )
            .distinct()
        )

    def save(self, *args, **kwargs):
        if self.commentary:
            self.plain_commentary = make_plain_text(self.commentary.content)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_display_name_option_c()


Testimonium.init_text_object_fields()
