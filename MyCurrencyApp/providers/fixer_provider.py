import logging
import requests
from .base_provider import BaseProvider
from ..enums.available_currencies import AvailableCurrencies


class FixerProvider(BaseProvider):
    def __init__(self, provider_model, url):
        super().__init__(provider_model, url)

    def get_exchange_rate_data(
        self, source_currency, exchanged_currency, valuation_date
    ):
        """
        Get the exchange rate from Fixer API.
        """
        params = {
            "base": source_currency,
            "symbols": (
                exchanged_currency
                if exchanged_currency
                else ",".join(AvailableCurrencies.CURRENCIES)
            ),
            "access_key": self.api_key,
        }
        try:
            response = requests.get(self.url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            if not data.get("success", True) and data.get("error").get("code") == 105:
                logging.warning(
                    f"Provider only supports {self.base_currency} as base. Adjusting rates for {source_currency}."
                )
                params["symbols"] = ",".join(AvailableCurrencies.CURRENCIES)
                data = self.get_adjusted_rates(source_currency, params)

                return {
                    "source_currency": source_currency,
                    "exchanged_currency": exchanged_currency,
                    "rates": data.get("rates", []),
                    "valuation_date": (
                        data.get("date") if data.get("date") else valuation_date
                    ),
                }

            return {
                "source_currency": source_currency,
                "exchanged_currency": exchanged_currency,
                "rates": data.get("rates", []),
                "valuation_date": valuation_date,
            }
        except Exception as e:
            logging.error(f"Error fetching data from FixerProvider: {e}")
            return None

    def get_adjusted_rates(self, target_base_currency, params={}):
        """
        Fetches rates with a default base currency and recalculates them to use the desired base currency.

        Returns:
            dict: A dictionary of rates adjusted to the desired base currency.
        """
        try:
            params["base"] = self.base_currency
            response = requests.get(self.url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            rates = data.get("rates", {})
            if target_base_currency not in rates:
                logging.info(
                    f"Desired base currency '{target_base_currency}' not found in the response."
                )
                return {"rates": {}}

            target_base_rate = rates[target_base_currency]

            adjusted_rates = {}
            for currency, rate in rates.items():
                if currency != target_base_currency:
                    adjusted_rates[currency] = rate / target_base_rate

            return {"rates": adjusted_rates}

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching data from provider: {e}")
            return {"rates": {}}
