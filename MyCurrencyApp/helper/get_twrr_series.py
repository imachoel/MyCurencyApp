from datetime import datetime
from decimal import Decimal

from ..models import Currency, CurrencyExchangeRate, CurrencyProvider
import logging

from ..utils import (
    get_date_range,
    get_provider_instance,
    update_exchange_rate_activity,
)


def calculate_twrr(source_currency_code, exchanged_currency_code, amount, start_date):
    """
    Retrieves historical exchange rates and calculates the Time-Weighted Rate of Return (TWRR).

    Parameters:
    - source_currency_code (str): The source currency code (e.g., "USD").
    - exchanged_currency_code (str): The exchanged currency code (e.g., "EUR").
    - amount (float): The amount invested.
    - start_date (str): The start date of the investment.

    Returns:
    - A list of dictionaries containing historical TWRR values.
    """
    # Retrieve valuation dates from start_date until today
    valuation_dates = get_date_range(start_date, datetime.today().strftime("%Y-%m-%d"))

    # Query existing historical rates from the database
    existing_rates = CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency_code,
        target_currency__code=exchanged_currency_code,
        valuation_date__gte=start_date,
    ).order_by("valuation_date")

    # Prepare data for calculating TWRR
    existing_dates = set(
        rate.valuation_date.strftime("%Y-%m-%d") for rate in existing_rates
    )
    missing_dates = [date for date in valuation_dates if date not in existing_dates]

    # If any dates are missing, fetch rates from providers
    if missing_dates:
        new_rates = _fetch_and_save_from_providers(
            source_currency_code, exchanged_currency_code, missing_dates
        )
        existing_rates = list(existing_rates) + new_rates

    if not existing_rates:
        return None

    previous_rate_value = None
    twrr_series = []

    for rate in sorted(existing_rates, key=lambda x: x.valuation_date):
        rate_value = Decimal(rate.rate_value)
        valuation_date = rate.valuation_date.strftime("%Y-%m-%d")

        if previous_rate_value is None:
            twrr_value = 0
        else:
            twrr_value = (rate_value / previous_rate_value) - 1

        current_amount = Decimal(amount) * rate_value

        twrr_series.append(
            {
                "valuation_date": valuation_date,
                "rate_value": rate_value,
                "twrr": twrr_value,
                "amount": current_amount,
            }
        )

        # Update previous rate value for the next iteration
        previous_rate_value = rate_value

    return twrr_series


def _fetch_and_save_from_providers(
        source_currency_code, exchanged_currency_code, missing_dates
):
    """
    Fetches and saves exchange rates for missing dates from providers and returns the new rates.
    """
    source_currency = Currency.objects.get(code=source_currency_code)
    target_currency = Currency.objects.get(code=exchanged_currency_code)
    new_rates = []
    providers = CurrencyProvider.objects.filter(active=True).order_by("priority")

    for provider in providers:
        try:
            provider_instance = get_provider_instance(provider, provider.url)

            for valuation_date in missing_dates:
                provider_instance.set_url(provider.url, valuation_date)
                data = provider_instance.get_exchange_rate_data(
                    source_currency_code, exchanged_currency_code, valuation_date
                )

                if data and data.get("rates", []):
                    rate_value = data["rates"].get(exchanged_currency_code)
                    if rate_value:
                        new_rate = update_exchange_rate_activity(
                            source_currency,
                            target_currency,
                            rate_value,
                            datetime.strptime(valuation_date, "%Y-%m-%d").date(),
                            provider,
                        )
                        new_rates.append(new_rate)

        except Exception as e:
            logging.error(f"Error fetching from provider {provider.name}: {e}")
            continue

    return new_rates
