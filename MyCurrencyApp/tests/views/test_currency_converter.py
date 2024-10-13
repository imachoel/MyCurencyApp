from datetime import datetime, timedelta

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from decimal import Decimal
from unittest.mock import patch

from ...models import CurrencyProvider, CurrencyExchangeRate
from MyCurrencyApp.tests.confest import (
    create_source_currency,
    add_exchange_rate,
    delete_exchange_rate,
)


class CurrencyConverterViewTests(APITestCase):

    def setUp(self):
        self.provider = CurrencyProvider.objects.create(
            name="Mock", url="http://mock.url", active=True, priority=0
        )
        self.source_currency = create_source_currency("USD", "US Dollar")
        self.target_currency = create_source_currency("EUR", "Euro")
        self.rate_value = Decimal("1.09")

        # Define the base URL for your API
        self.url = reverse(
            "currency-converter"
        )  # Use the correct URL name for your view

    def test_missing_required_parameters(self):
        # Test with missing parameters
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required parameters", response.data["error"])

    def test_currencies_not_supported(self):
        # Test with unsupported currency codes
        response = self.client.get(
            self.url,
            {"source_currency": "ABC", "target_currency": "XYZ", "amount": "100"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Currencies not supported", response.data["error"])

    def test_invalid_amount_format(self):
        # Test with invalid amount format
        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "EUR", "amount": "invalid"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid amount format", response.data["error"])

    def test_negative_amount(self):
        # Test with negative amount
        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "EUR", "amount": "-100"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Amount must be greater than zero", response.data["error"])

    @patch(
        "MyCurrencyApp.helper.get_create_exchange_rate.get_or_create_exchange_rate"
    )  # Mock the function that fetches the exchange rate
    def test_exchange_rate_not_available(self, mock_get_exchange_rate):
        # Simulate exchange rate not available
        mock_get_exchange_rate.return_value = None
        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "ABC", "amount": "100"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_successful_currency_conversion_from_db(self):
        # Simulate a valid exchange rate
        add_exchange_rate(
            self.source_currency, self.target_currency, self.provider, rate_value=1.09
        )

        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "EUR", "amount": "100"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["target_currency"], "EUR")
        self.assertEqual(response.data["exchange_rate"], self.rate_value)
        self.assertEqual(response.data["amount"], Decimal("100"))
        self.assertEqual(
            response.data["converted_amount"], Decimal("100.00") * self.rate_value
        )

        delete_exchange_rate(self.source_currency, self.target_currency)

    def test_successful_currency_conversion_from_provider(self):
        delete_exchange_rate(self.source_currency, self.target_currency)
        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "EUR", "amount": "100"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["target_currency"], "EUR")
        self.assertTrue(0.85 <= response.data["exchange_rate"] <= 1.25)
        self.assertTrue(
            Decimal("100") * Decimal("0.85")
            <= response.data["converted_amount"]
            <= Decimal("100") * Decimal("1.25")
        )
        # Test that it has been updated with the latest exchange rate
        db_rate = CurrencyExchangeRate.objects.filter(
            source_currency__code="USD", target_currency__code="EUR", active=True
        ).first()
        self.assertEqual(
            round(Decimal(response.data["exchange_rate"]), 3),
            round(db_rate.rate_value, 3),
        )
        self.assertTrue(
            datetime.now().strftime("%Y-%m-%d")
            == db_rate.valuation_date.strftime("%Y-%m-%d")
        )

    @patch(
        "MyCurrencyApp.views.currency_converter_view.get_or_create_exchange_rate"
    )  # Mock the function that fetches the exchange rate
    def test_successful_currency_conversion_from_provider_if_database_rate_value_not_from_today(
            self, mock_get_exchange_rate
    ):
        add_exchange_rate(
            self.source_currency,
            self.target_currency,
            self.provider,
            rate_value=1.09,
            valuation_date=datetime.now() - timedelta(days=1),
        )
        mock_get_exchange_rate.return_value = Decimal("1.2")

        response = self.client.get(
            self.url,
            {"source_currency": "USD", "target_currency": "EUR", "amount": "100"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["target_currency"], "EUR")
        self.assertEqual(response.data["exchange_rate"], Decimal("1.2"))
        self.assertEqual(response.data["amount"], Decimal("100"))
        self.assertEqual(response.data["converted_amount"], Decimal("120.00"))
