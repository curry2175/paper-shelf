from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Paper, ReadingRecord


class PaperShelfSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reader", email="reader@example.com", password="safe-pass-123"
        )
        self.paper = Paper.objects.create(
            pmid="12345678",
            title="Example medical paper",
            journal="Example Journal",
            publication_date="2026 Jul",
            pubmed_url="https://pubmed.ncbi.nlm.nih.gov/12345678/",
            abstract="This is an example abstract.",
        )

    def test_public_home_and_signup_render(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("signup")).status_code, 200)

    def test_authenticated_pages_render(self):
        self.client.login(username="reader", password="safe-pass-123")
        self.assertEqual(self.client.get(reverse("papers:search")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("papers:detail", args=[self.paper.pk])).status_code,
            200,
        )
        self.assertEqual(self.client.get(reverse("papers:bookshelf")).status_code, 200)

    def test_mark_read_adds_one_unique_record(self):
        self.client.login(username="reader", password="safe-pass-123")
        url = reverse("papers:mark_read", args=[self.paper.pk])
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(
            ReadingRecord.objects.filter(user=self.user, paper=self.paper).count(), 1
        )

import json
from unittest.mock import patch

from .models import ExtensionToken
from .tokens import issue_extension_token


class ExtensionApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="extension-reader",
            email="extension@example.com",
            password="safe-pass-123",
        )
        self.token = issue_extension_token(self.user)
        self.endpoint = reverse("papers:api_save_reading_record")
        self.paper_payload = {
            "pmid": "42472515",
            "doi": "10.1000/example",
            "title": "Saved from an extension",
            "journal": "Example Journal",
            "source_url": "https://pubmed.ncbi.nlm.nih.gov/42472515/",
            "note": "Important paper",
        }
        self.pubmed_result = {
            "pmid": "42472515",
            "title": "Saved from an extension",
            "authors": "Example A, Example B",
            "journal": "Example Journal",
            "publication_date": "2026 Jul",
            "doi": "10.1000/example",
            "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/42472515/",
            "abstract": "Example abstract",
        }

    def test_extension_settings_requires_login(self):
        response = self.client.get(reverse("papers:extension_settings"))
        self.assertEqual(response.status_code, 302)

    def test_token_is_stored_as_digest_not_plaintext(self):
        record = ExtensionToken.objects.get(user=self.user)
        self.assertNotIn(self.token, record.verifier_digest)
        self.assertEqual(len(record.verifier_digest), 64)

    @patch("papers.views.find_paper_for_extension")
    def test_extension_can_save_a_reading_record(self, mocked_find):
        mocked_find.return_value = self.pubmed_result
        response = self.client.post(
            self.endpoint,
            data=json.dumps(self.paper_payload),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(
            ReadingRecord.objects.filter(user=self.user, paper__pmid="42472515").count(),
            1,
        )

    def test_invalid_token_is_rejected(self):
        response = self.client.post(
            self.endpoint,
            data=json.dumps(self.paper_payload),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer ps_invalid_invalid",
        )
        self.assertEqual(response.status_code, 401)

    def test_preflight_has_cors_headers(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")


from django.core import mail
from django.test import override_settings


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountRecoveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="forgotten-reader",
            email="forgotten@example.com",
            password="old-password-123",
        )

    def test_login_page_links_to_account_recovery(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, reverse("account_recovery"))

    def test_username_recovery_sends_username_by_email(self):
        response = self.client.post(
            reverse("username_recovery"),
            {"email": self.user.email},
        )
        self.assertRedirects(response, reverse("username_recovery_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.username, mail.outbox[0].body)

    def test_username_recovery_does_not_reveal_unknown_email(self):
        response = self.client.post(
            reverse("username_recovery"),
            {"email": "unknown@example.com"},
        )
        self.assertRedirects(response, reverse("username_recovery_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_sends_one_time_link(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": self.user.email},
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/account/reset/", mail.outbox[0].body)
