from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch
from datetime import datetime
from django.contrib.auth.models import User
from MyCurrencyApp.models import Currency


class ExchangeRateGraphAdminTests(TestCase):
    def setUp(self):
        # Set up initial data for testing
        self.url_graph_view = reverse("admin:exchange_rate_graph")
        self.url_all_currencies = reverse("admin:exchange_rate_all_currencies")
        # Create a superuser to access the admin interface
        self.user = User.objects.create_superuser(
            username="admin", password="password", email="admin@example.com"
        )
        self.client.login(username="admin", password="password")

        # Create currencies for testing
        self.source_currency = Currency.objects.create(code="USD", name="US Dollar")
        self.target_currency = Currency.objects.create(code="EUR", name="Euro")

    def test_access_graph_view(self):
        # Test that the graph view is accessible
        response = self.client.get(self.url_graph_view)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/exchange_rate_graph.html")
        self.assertIn("form", response.context)

    def test_exchange_rate_all_currencies_with_valid_dates(self):
        # Test fetching exchange rates with valid dates
        response = self.client.get(self.url_all_currencies, {
            "start_date": "2023-10-01",
            "end_date": "2023-10-31"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json())

    def test_exchange_rate_all_currencies_with_invalid_dates(self):
        # Test fetching exchange rates with an invalid date format
        response = self.client.get(self.url_all_currencies, {
            "start_date": "invalid-date",
            "end_date": "2023-10-31"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
        self.assertEqual(response.json()["error"], "Invalid date format")

    @patch("MyCurrencyApp.admin_views.graph_view_admin.get_currency_rates_data")
    @patch("MyCurrencyApp.admin_views.graph_view_admin.format_data_for_chart")
    def test_exchange_rate_all_currencies_data_formatting(
            self, mock_format_data_for_chart, mock_get_currency_rates_data
    ):
        # Mock the data returned from get_currency_rates_data
        mock_get_currency_rates_data.return_value = [
            {"date": "2023-10-01", "rate": 1.1},
            {"date": "2023-10-02", "rate": 1.2},
        ]

        # Mock the formatted data for the chart
        mock_format_data_for_chart.return_value = {
            "USD": [{"date": "2023-10-01", "rate": 1.1}, {"date": "2023-10-02", "rate": 1.2}]
        }

        response = self.client.get(self.url_all_currencies, {
            "start_date": "2023-10-01",
            "end_date": "2023-10-31"
        })
        self.assertEqual(response.status_code, 200)

        # Verify that the data is formatted correctly in the response
        self.assertEqual(response.json()["data"]["USD"], [
            {"date": "2023-10-01", "rate": 1.1},
            {"date": "2023-10-02", "rate": 1.2},
        ])
