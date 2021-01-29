import pytest
from django.test import TestCase
from django.urls import reverse

from rard.research.models import Testimonium, TextObjectField

pytestmark = pytest.mark.django_db


class TestTestimonium(TestCase):

    def test_creation(self):
        # can create with a name only
        data = {
            'name': 'name',
        }
        testimonium = Testimonium.objects.create(**data)
        self.assertEqual(testimonium.name, data['name'])

    def test_required_fields(self):
        # required on forms
        self.assertFalse(Testimonium._meta.get_field('name').blank)

        # not required on forms
        self.assertTrue(Testimonium._meta.get_field('images').blank)

    def test_display(self):
        # the __str__ function should show the name
        data = {
            'name': 'name',
        }
        testimonium = Testimonium.objects.create(**data)
        self.assertEqual(
            str(testimonium), 'Unlinked {}'.format(testimonium.pk)
        )

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

    def test_get_absolute_url(self):
        testimonium = Testimonium.objects.create(name='name')
        self.assertEqual(
            testimonium.get_absolute_url(),
            reverse('testimonium:detail', kwargs={'pk': testimonium.pk})
        )
