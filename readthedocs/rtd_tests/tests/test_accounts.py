from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from registration.models import RegistrationProfile

from core.models import UserProfile


class AccountRegistrationTests(TestCase):

    def setUp(self):
        self.username = 'testuser'
        self.email = 'test@test.com'
        self.password = 'test_password'

    def register(self):
        """POSTs to the registration URL."""
        return self.client.post('/accounts/signup/', {
            'username': self.username,
            'email': self.email,
            'password1': self.password,
            'password2': self.password,
        })

    def test_register_account(self):
        """
        Test that users can use the login page to register.
        """
        response = self.register()

        user = User.objects.get(username=self.username)

        self.assertEqual(user.username, self.username)
        self.assertEqual(user.email, self.email)

    def test_sends_activation_email(self):
        """
        Test that users get activation emails.
        """
        self.register()

        self.assertEqual(len(mail.outbox), 1)

        message = mail.outbox[0]
        self.assertIn(self.email, message.to)
        self.assertIn('confirm', message.subject.lower())

    def test_creates_profile(self):
        """
        Test that a profile is created.
        """
        self.register()

        user = User.objects.get(username=self.username)
        profile = user.profile.get()

        self.assertIsNotNone(profile)
        self.assertIsInstance(profile, UserProfile)


class AccountMigrationTests(TestCase):

    def setUp(self):
        self.username = 'testuser'
        self.email = 'test@test.com'
        self.password = 'test_password'

    def test_old_activation_links_still_work(self):
        """
        Test that django-registration activation links can still be used.

        This test can be safely removed once the migration to django-allauth
        is complete and no outstanding activation links exist. See
        settings.ACCOUNT_ACTIVATION_DAYS to find out when that will be.
        """
        user = RegistrationProfile.objects.create_inactive_user(
            username=self.username,
            email=self.email,
            password=self.password,
            site=Site.objects.get_current(),
        )
        registration = RegistrationProfile.objects.get(user=user)

        self.assertFalse(user.is_active)

        self.client.get(reverse(
            'registration_activate',
            kwargs={'activation_key': registration.activation_key},
        ))

        self.assertTrue(User.objects.get(id=user.id).is_active)
