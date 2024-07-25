from django.test import TestCase

from rard.research.models import (
    Antiquarian,
    CitingWork,
    ConcordanceModel,
    Edition,
    Fragment,
    OriginalText,
    PartIdentifier,
)
from rard.research.models.base import FragmentLink


class TestConcordanceModel(TestCase):
    def setUp(self):
        self.fragment = Fragment.objects.create(name="name")
        self.citing_work = CitingWork.objects.create(title="title")
        self.original_text = OriginalText.objects.create(
            owner=self.fragment, citing_work=self.citing_work
        )
        self.edition = Edition.objects.create(name="first_edition")
        self.identifier = PartIdentifier.objects.create(
            edition=self.edition, value="initial part"
        )
        self.creation_data = {
            "reference": "55.l",
            "content_type": "F",
            "identifier": self.identifier,
        }

    def test_creation(self):
        data = self.creation_data

        concordance = ConcordanceModel.objects.create(
            **data, original_text=self.original_text
        )
        for key, val in data.items():
            self.assertEqual(getattr(concordance, key), val)

    def test_concordance_identifiers(self):
        # test the names to go in the ConcordanceModel table including ordinals
        # set up a second original text
        OriginalText.objects.create(owner=self.fragment, citing_work=self.citing_work)
        a = Antiquarian.objects.create(name="name1", re_code="name1")
        link = FragmentLink.objects.create(fragment=self.fragment, antiquarian=a)

        concordances = link.get_concordance_identifiers()
        self.assertEqual(
            [x[0] for x in self.original_text.concordances.all()],
            concordances,
        )
