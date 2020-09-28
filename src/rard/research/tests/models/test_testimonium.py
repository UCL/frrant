import pytest
from django.test import TestCase

from rard.research.models import Testimonium, TextObjectField

pytestmark = pytest.mark.django_db


class TestTestimonium(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        testimonium = Testimonium.objects.create(**data)
        self.assertEqual(testimonium.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Testimonium._meta.get_field('name').blank)

        # not required on forms
        self.assertTrue(
            Testimonium._meta.get_field('apparatus_criticus').blank
        )
        self.assertTrue(Testimonium._meta.get_field('images').blank)
        self.assertTrue(Testimonium._meta.get_field('definite_works').blank)
        self.assertTrue(Testimonium._meta.get_field('possible_works').blank)
        self.assertTrue(
            Testimonium._meta.get_field('definite_antiquarians').blank
        )
        self.assertTrue(
            Testimonium._meta.get_field('possible_antiquarians').blank
        )

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
            'apparatus_criticus': 'app_criticus',
        }
        testimonium = Testimonium.objects.create(**data)
        self.assertEqual(str(testimonium), data['name'])

    def test_initial_images(self):
        testimonium = Testimonium.objects.create(name='name')
        self.assertEqual(testimonium.images.count(), 0)

    def test_commentary_created(self):
        testimonium = Testimonium.objects.create(name='name')
        self.assertIsNotNone(testimonium.commentary.pk)
        self.assertEqual(
            TextObjectField.objects.get(pk=testimonium.commentary.pk),
            testimonium.commentary
        )

    def test_commentary_deleted(self):
        testimonium = Testimonium.objects.create(name='name')
        commentary_pk = testimonium.commentary.pk
        testimonium.delete()
        with self.assertRaises(TextObjectField.DoesNotExist):
            TextObjectField.objects.get(pk=commentary_pk)

    # def test_detail_url(self):
    #     testimonium = Testimonium.objects.create(name='name')
    #     self.assertEqual(
    #         testimonium.get_detail_url(),
    #         reverse('testimonium:detail', kwargs={'pk': testimonium.pk})
    #     )
