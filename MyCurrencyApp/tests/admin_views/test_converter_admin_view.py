from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from MyCurrencyApp.forms.converter_form import CurrencyConverterForm
from MyCurrencyApp.models import Currency


class ConverterAdminTests(TestCase):
    def setUp(self):
        self.url = reverse("admin:currency_converter")
        self.source_currency = Currency.objects.create(code="USD", name="US Dollar")
        self.target_currency = Currency.objects.create(code="EUR", name="Euro")
        self.user = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.client.login(username="admin", password="password")

    def test_access_converter_view(self):
        # Test that the converter view is accessible
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/converter.html")
        self.assertIsInstance(response.context["form"], CurrencyConverterForm)

    def test_converter_view_with_valid_data(self):
        # Test conversion with valid data
        response = self.client.post(
            self.url,
            {
                "source_currency": self.source_currency.id,
                "target_currencies": [self.target_currency.id],
                "amount": "100",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("conversion_result", response.context)

        # Check if the conversion result is a dictionary
        conversion_result = response.context["conversion_result"]
        self.assertIsInstance(conversion_result, dict)

    @patch("MyCurrencyApp.admin_views.converter_admin.get_or_create_exchange_rate")
    def test_converter_view_with_mocked_exchange_rate(self, mock_get_exchange_rate):
        # Mock the exchange rate to simulate a known conversion rate
        mock_get_exchange_rate.return_value = Decimal("1.1")

        response = self.client.post(
            self.url,
            {
                "source_currency": self.source_currency.id,
                "target_currencies": [self.target_currency.id],
                "amount": "100",
            },
        )
        self.assertEqual(response.status_code, 200)

        # Verify the conversion result
        conversion_result = response.context["conversion_result"]
        expected_amount = Decimal("100") * Decimal("1.1")
        self.assertEqual(conversion_result["EUR"], expected_amount)

    def test_converter_view_same_currency(self):
        # Test conversion where source and target currencies are the same
        response = self.client.post(
            self.url,
            {
                "source_currency": self.source_currency.id,
                "target_currencies": [self.source_currency.id],
                "amount": "100",
            },
        )
        self.assertEqual(response.status_code, 200)

        # Verify that the converted amount equals the original amount
        conversion_result = response.context["conversion_result"]
        self.assertEqual(conversion_result["USD"], Decimal("100"))

    @patch("MyCurrencyApp.admin_views.converter_admin.get_or_create_exchange_rate")
    def test_converter_view_with_exchange_rate_failure(self, mock_get_exchange_rate):
        # Simulate a failure in retrieving the exchange rate
        mock_get_exchange_rate.return_value = None

        response = self.client.post(
            self.url,
            {
                "source_currency": self.source_currency.id,
                "target_currencies": [self.target_currency.id],
                "amount": "100",
            },
        )
        self.assertEqual(response.status_code, 200)

        # Verify that an error message is returned for the target currency
        conversion_result = response.context["conversion_result"]
        self.assertEqual(conversion_result["EUR"], "Error fetching data")
