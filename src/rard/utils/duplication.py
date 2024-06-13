from bs4 import BeautifulSoup

from rard.research.models import (
    ApparatusCriticusItem,
    Concordance,
    OriginalText,
    Translation,
)


def duplicate_original_text(original):
    # Create a dictionary to hold the values for the new OriginalText object
    new_original_text_data = {}

    # Iterate over the fields of the OriginalText model
    for field in original._meta.fields:
        # Exclude the ID field
        if field.name in ["id", "created", "modified"]:
            continue

        field_value = getattr(original, field.name)

        new_original_text_data[field.name] = field_value

    # Create a new OT object with the copied values
    new_original_text = OriginalText.objects.create(**new_original_text_data)
    return new_original_text


def copy_concordances_apcrit_and_translations(original, new_original_text):
    # Copy relationships to Concordances, Ap Crit & Translations
    model_details = {
        Concordance: {
            "filter_name": "original_text",
            "filter_value": original,
            "ot_fieldname": "original_text",
        },
        ApparatusCriticusItem: {
            "filter_name": "original_text",
            "filter_value": original.pk,
            "ot_fieldname": "parent",
        },
        Translation: {
            "filter_name": "original_text",
            "filter_value": original,
            "ot_fieldname": "original_text",
        },
    }

    for model_class in model_details.keys():
        model_info = model_details[model_class]
        filter_name = model_info["filter_name"]
        filter_value = model_info["filter_value"]
        ot_fieldname = model_info["ot_fieldname"]

        new_model_data = {}
        for original_item in model_class.objects.filter(**{filter_name: filter_value}):
            for field in original_item._meta.fields:
                # Exclude some fields
                if field.name in [
                    "id",
                    "created",
                    "modified",
                    ot_fieldname,
                    "content_type",
                    "object_id",
                ]:
                    continue

                field_value = getattr(original_item, field.name)
                new_model_data[field.name] = field_value

            new_model_data[
                ot_fieldname
            ] = new_original_text  # make sure to assign new OT in place of the old one (field skipped above)

            model_class.objects.create(**new_model_data)


def update_ot_content_references(new_original_text):
    # use beautifulsoup to update the references in the ot content
    soup = BeautifulSoup(new_original_text.content, features="html.parser")
    mentions = soup.find_all(
        "span", class_="mention", attrs={"data-denotation-char": "#"}
    )
    apcriti = new_original_text.apparatus_criticus_items.all()

    for mention, apcrit in zip(mentions, apcriti):
        mention["data-id"] = apcrit.pk
        mention["data-original-text"] = new_original_text.pk
        mention["data-parent"] = new_original_text.pk

    updated_content = str(soup)

    new_original_text.content = updated_content
    new_original_text.save()
