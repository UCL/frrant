from django.db import models


class Reference(models.Model):
    # e.g. page 24
    text = models.CharField(max_length=128, blank=False)

    # The value 24 to be used in 'ordering by reference' taking example above
    # In some cases it will be a dot-separated list of numbers that also need
    # to be used for ordering, like 1.3.24.
    order = models.CharField(blank=False, null=True, default=None, max_length=100)

    original_text = models.ForeignKey(
        "OriginalText",
        on_delete=models.CASCADE,
        default=None,
        related_name="references",
    )
