import random
from .base_provider import BaseProvider
from ..models import Currency


class MockProvider(BaseProvider):
    def __init__(self, provider_model, url):
        super().__init__(provider_model, url)

    def get_exchange_rate_data(
            self, source_currency, exchanged_currency, valuation_date
    ):
        """
        Simulate getting exchange rates for the given source currency.
        """
        # Retrieve all available currencies excluding the source currency
        currencies = Currency.objects.exclude(code=source_currency).values_list(
            "code", flat=True
        )

        # Create a dictionary to hold the rates
        rates = {}

        # Simulate exchange rates for each currency against the source currency
        for exchanged_currency in currencies:
            rates[exchanged_currency] = random.uniform(
                0.85, 1.25
            )  # Random rate for testing

        return {
            "source_currency": source_currency,
            "exchanged_currency": exchanged_currency,  # You can set this if needed
            "rates": rates,
            "valuation_date": valuation_date,
        }
