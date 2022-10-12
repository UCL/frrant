from django.db import models


class Reference(models.Model):
    # e.g. Jones/James
    editor = models.CharField(max_length=128, blank=True)

    # The value to be used to refer to the position in the text
    # In some cases it will be a dot-separated list of numbers eg. 2.6-8
    reference_position = models.CharField(blank=False, max_length=128)

    original_text = models.ForeignKey(
        "OriginalText",
        on_delete=models.CASCADE,
        default=None,
        related_name="references",
    )
