from django.test import TestCase

from django.contrib.auth.models import User


class ProfileTests(TestCase):
    fixtures = ['eric.json']

    def test_profile_page(self):
        """
        Test that a user's profile is provided to the profile detail template.
        """
        user = User.objects.get(username='eric')

        response = self.client.get('/profiles/eric/', follow_redirects=True)

        self.assertEqual(response.context['profile'], user.profile.get())
