from datetime import datetime
from decimal import Decimal

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch

from MyCurrencyApp.models import CurrencyExchangeRate, CurrencyProvider
from MyCurrencyApp.tests.confest import (
    create_source_currency,
    add_exchange_rate,
    delete_exchange_rate,
)
from MyCurrencyApp.utils import get_date_range


class CurrencyRatesListViewTests(APITestCase):

    def setUp(self):
        # Create currencies for the tests
        self.source_currency = create_source_currency("USD", "US Dollar")
        self.target_currency = create_source_currency("EUR", "Euro")
        self.provider = CurrencyProvider.objects.create(
            name="Mock", url="http://mock.url", active=True, priority=0
        )
        self.url = reverse(
            "currency-rates"
        )  # Make sure this is the correct URL name for your view

    def test_missing_parameters(self):
        # Test when required parameters are missing
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required parameters", response.data["error"])

    def test_unsupported_currency(self):
        # Test when an unsupported currency is provided
        response = self.client.get(
            self.url,
            {
                "source_currency": "ABC",
                "date_from": "2023-10-01",
                "date_to": "2023-10-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Currencies not supported", response.data["error"])

    @patch("MyCurrencyApp.views.currency_rates_list_view.get_currency_rates_data")
    def test_no_exchange_rates_found(self, mock_get_currency_rates_data):
        # Mock the function to return an empty response, simulating no rates found
        mock_get_currency_rates_data.return_value = None

        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "date_from": "2023-10-01",
                "date_to": "2023-10-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No rates found", response.data["error"])

    @patch("MyCurrencyApp.views.currency_rates_list_view.get_currency_rates_data")
    def test_unexpected_error_handling(self, mock_get_currency_rates_data):
        mock_get_currency_rates_data.side_effect = Exception("Unexpected error")

        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "date_from": "2023-10-01",
                "date_to": "2023-10-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(
            "An error occurred while processing the request.", response.data["error"]
        )

    def test_successful_currency_rate_retrieval_from_mock_provider(self):
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "date_from": "2023-10-01",
                "date_to": "2023-10-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        date_from_dt = datetime.strptime("2023-10-01", "%Y-%m-%d")
        date_to_dt = datetime.strptime("2023-10-31", "%Y-%m-%d")

        for currency, rates in response.data.items():
            for rate in rates:
                # Parse the valuation_date as a datetime object
                valuation_date = datetime.strptime(rate["valuation_date"], "%Y-%m-%d")

                # Assert that the valuation_date is within the specified range
                self.assertTrue(date_from_dt <= valuation_date <= date_to_dt)

                # Assert that the rate_value is within the specified Mock Provider range (0.85 to 1.25)
                self.assertTrue(0.85 <= rate["rate_value"] <= 1.25)
                # Query the database for the matching exchange rate
                db_rate = CurrencyExchangeRate.objects.filter(
                    source_currency__code="USD",
                    target_currency__code="EUR",
                    valuation_date=valuation_date,
                ).first()

                self.assertEqual(
                    round(Decimal(rate["rate_value"]), 3), round(db_rate.rate_value, 3)
                )

    def test_successful_currency_rate_retrieval_from_db(self):
        delete_exchange_rate(self.source_currency, self.target_currency)
        range_dates = get_date_range("2023-10-01", "2023-10-31")

        for valuation_date in range_dates:
            add_exchange_rate(
                self.source_currency,
                self.target_currency,
                self.provider,
                valuation_date=valuation_date,
            )
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "date_from": "2023-10-01",
                "date_to": "2023-10-31",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_rates = response.data["EUR"]

        for index, response_rate in enumerate(response_rates):
            valuation_date = response_rate["valuation_date"]

            db_rate = CurrencyExchangeRate.objects.filter(
                source_currency__code=self.source_currency.code,
                target_currency__code=self.target_currency.code,
                valuation_date=valuation_date,
            ).first()

            self.assertEqual(
                round(db_rate.rate_value, 3),
                round(Decimal(response_rate["rate_value"]), 3),
            )
