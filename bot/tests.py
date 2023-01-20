from django.test import TestCase
from .models import Redditor

# Create your tests here.


class RedditorTestCase(TestCase):
    def setUp(self):
        Redditor.objects.create(name='test-redditor')

    def test_redditor_exists(self):
        redditor = Redditor.objects.get(name='test-redditor')
        self.assertEqual(redditor.name, 'test-redditor')
