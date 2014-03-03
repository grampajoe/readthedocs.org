from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from allauth.account.models import EmailConfirmation
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
        }, follow=True)

    def confirm_email_and_logout(self):
        """Confirms the user's email and logs out."""
        user = User.objects.get(username=self.username)
        confirmation = EmailConfirmation.objects.get(email_address__user=user)

        self.client.post(
            reverse('account_confirm_email', kwargs={'key': confirmation.key}),
        )

        self.client.logout()

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

    def test_register_page_text(self):
        """
        Ensure the signup page hasn't changed much.
        """
        response = self.client.get('/accounts/signup/')

        self.assertIn('Register for an account', response.content)

    def test_can_log_in(self):
        """
        Test logging in!
        """
        self.register()

        self.confirm_email_and_logout()

        # Get the login page
        response = self.client.get('/accounts/login/', follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['request'].user.is_authenticated())

        # Submit the login form
        response = self.client.post('/accounts/login/', {
            'login': self.username,
            'password': self.password,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['request'].user.is_authenticated())


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
