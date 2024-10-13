import logging

from ..models import CurrencyExchangeRate, CurrencyProvider, Currency
from ..utils import get_date_range, get_provider_instance, update_exchange_rate_activity


def get_currency_rates_data(source_currency_code, date_from, date_to):
    """
    Retrieves exchange rate data for a specified source currency and date range.
    If rates for some dates are missing, they are fetched from external providers.

    Args:
        source_currency_code (str): The code of the source currency.
        date_from (str): The start date of the range in "YYYY-MM-DD" format.
        date_to (str): The end date of the range in "YYYY-MM-DD" format.

    Returns:
        dict: A dictionary containing exchange rate data, organized by target currency.
    """
    valuation_dates = get_date_range(date_from, date_to)

    existing_rates = CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency_code,
        valuation_date__range=[date_from, date_to],
    ).order_by("valuation_date")
    response_data = {}

    for rate in existing_rates:
        if rate.target_currency.code not in response_data:
            response_data[rate.target_currency.code] = []
        response_data[rate.target_currency.code].append(
            {"rate_value": rate.rate_value, "valuation_date": rate.valuation_date}
        )

    existing_dates = set(
        rate.valuation_date.strftime("%Y-%m-%d") for rate in existing_rates
    )
    missing_dates = [date for date in valuation_dates if date not in existing_dates]

    if missing_dates:
        response_data.update(
            _fetch_and_save_from_providers(source_currency_code, missing_dates)
        )

    return response_data


def _fetch_and_save_from_providers(source_currency_code, missing_dates):
    """
    Retrieves exchange rates for missing dates from active providers and saves them to the database.

    Args:
        source_currency_code (str): The code of the source currency.
        missing_dates (list): List of dates for which exchange rates are missing.

    Returns:
        dict: A dictionary containing exchange rate data by target currency.
    """
    response_data = {}
    providers = CurrencyProvider.objects.filter(active=True).order_by("priority")

    for provider in providers:
        try:
            provider_instance = get_provider_instance(provider, provider.url)

            for valuation_date in missing_dates:
                provider_instance.set_url(provider.url, valuation_date)
                data = provider_instance.get_exchange_rate_data(
                    source_currency_code, "", valuation_date
                )
                rates = data.get("rates", {})

                if data and rates:
                    for target_currency in rates:
                        rate_value = rates[target_currency]
                        if target_currency not in response_data:
                            response_data[target_currency] = []
                        response_data[target_currency].append(
                            {
                                "rate_value": rate_value,
                                "valuation_date": data.get("valuation_date"),
                            }
                        )

            if response_data:
                _process_update_exchange_rate_activity(
                    source_currency_code, provider, response_data
                )
                break

        except Exception as e:
            logging.error(f"Error fetching from provider {provider.name}: {e}")
            continue

    return response_data


def _process_update_exchange_rate_activity(source_currency_code, provider, new_data):
    """
    Updates exchange rate activity records in the database for the given source currency,
    provider, and new exchange rate data.

    Args:
        source_currency_code (str): The code of the source currency.
        provider (CurrencyProvider): The provider from which the rates were fetched.
        new_data (dict): The newly fetched exchange rate data, organized by target currency.
    """
    source_currency = Currency.objects.get(code=source_currency_code)

    for target_currency_code, rates in new_data.items():
        target_currency = Currency.objects.get(code=target_currency_code)

        for entry in rates:
            valuation_date = entry.get("valuation_date")
            rate_value = entry.get("rate_value")

            update_exchange_rate_activity(
                source_currency,
                target_currency,
                rate_value,
                valuation_date,
                provider,
            )
