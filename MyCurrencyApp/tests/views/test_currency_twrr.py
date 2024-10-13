from datetime import datetime, timedelta
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


class CurrencyTWRRViewTests(APITestCase):

    def setUp(self):
        # Create currencies for the tests
        self.source_currency = create_source_currency("USD", "US Dollar")
        self.target_currency = create_source_currency("EUR", "Euro")
        self.provider = CurrencyProvider.objects.create(
            name="Mock", url="http://mock.url", active=True, priority=0
        )
        self.url = reverse(
            "currency-twrr"
        )  # Make sure this is the correct URL name for your TWRR view

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
                "exchanged_currency": "XYZ",
                "amount": "1000",
                "start_date": "2023-10-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Currencies not supported", response.data["error"])

    def test_invalid_amount_format(self):
        # Test when the amount is not a valid number
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "not-a-number",
                "start_date": "2023-10-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid amount format", response.data["error"])

    def test_amount_must_be_greater_than_zero(self):
        # Test when the amount is zero or negative
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "-100",
                "start_date": "2023-10-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Amount must be greater than zero", response.data["error"])

    @patch("MyCurrencyApp.views.currency_twrr_view.calculate_twrr")
    def test_no_twrr_series_found(self, mock_calculate_twrr):
        # Mock the calculate_twrr function to return an empty response, simulating no TWRR data found
        mock_calculate_twrr.return_value = None

        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "1000",
                "start_date": "2023-10-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(
            "No historical exchange rates available for the given parameters",
            response.data["error"],
        )

    @patch("MyCurrencyApp.views.currency_twrr_view.calculate_twrr")
    def test_unexpected_error_handling(self, mock_calculate_twrr):
        # Mock the calculate_twrr function to raise an exception
        mock_calculate_twrr.side_effect = Exception("Unexpected error")

        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "1000",
                "start_date": "2023-10-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn(
            "An error occurred while calculating TWRR", response.data["error"]
        )

    def test_successful_twrr_calculation_from_db(self):
        # Add mock exchange rates for the test
        delete_exchange_rate(self.source_currency, self.target_currency)
        start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        range_dates = get_date_range(start_date, datetime.now().strftime("%Y-%m-%d"))
        for valuation_date in range_dates:
            add_exchange_rate(
                self.source_currency,
                self.target_currency,
                self.provider,
                valuation_date=valuation_date,
            )

        # Test successful TWRR calculation
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "1000",
                "start_date": start_date,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("twrr_series", response.data)
        self.assertEqual(len(response.data["twrr_series"]), len(range_dates))
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["exchanged_currency"], "EUR")
        self.assertEqual(Decimal(response.data["amount_invested"]), Decimal("1000"))
        self.assertEqual(response.data["start_date"], start_date)

    def test_successful_twrr_calculation_from_provider(self):
        # Add mock exchange rates for the test
        delete_exchange_rate(self.source_currency, self.target_currency)
        start_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        range_dates = get_date_range(start_date, datetime.now().strftime("%Y-%m-%d"))

        # Test successful TWRR calculation
        response = self.client.get(
            self.url,
            {
                "source_currency": "USD",
                "exchanged_currency": "EUR",
                "amount": "1000",
                "start_date": start_date,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("twrr_series", response.data)
        self.assertEqual(len(response.data["twrr_series"]), len(range_dates))
        self.assertEqual(response.data["source_currency"], "USD")
        self.assertEqual(response.data["exchanged_currency"], "EUR")
        self.assertEqual(Decimal(response.data["amount_invested"]), Decimal("1000"))
        self.assertEqual(response.data["start_date"], start_date)

        response_rates = response.data["twrr_series"]

        for index, response_rate in enumerate(response_rates):
            valuation_date = response_rate["valuation_date"]

            db_rate = CurrencyExchangeRate.objects.filter(
                source_currency__code=self.source_currency.code,
                target_currency__code=self.target_currency.code,
                valuation_date=valuation_date,
            ).first()

            self.assertEqual(
                round(db_rate.rate_value, 4),
                round(Decimal(response_rate["rate_value"]), 4),
            )
