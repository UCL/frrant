from django.db import models
from django.utils.translation import gettext as _

from rard.utils.basemodel import BaseModel


class CitingWork(BaseModel):

    # allow blank name as may be anonymous
    author = models.CharField(max_length=256, blank=True)

    title = models.CharField(max_length=256, blank=False)

    edition = models.CharField(max_length=128, blank=True)

    def __str__(self):
        tokens = [
            self.author if self.author else _('Anonymous'),
            self.title,
            self.edition
        ]
        return ', '.join([t for t in tokens if t])

    def fragments(self):
        from rard.research.models import Fragment
        return Fragment.objects.filter(
            original_texts__citing_work=self
        ).distinct()

    def testimonia(self):
        from rard.research.models import Testimonium
        return Testimonium.objects.filter(
            original_texts__citing_work=self
        ).distinct()
