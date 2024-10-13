import logging
from datetime import datetime
from decimal import Decimal

from django.utils.timezone import now

from ..enums.endpoint_type import EndpointType
from ..models import Currency, CurrencyExchangeRate, CurrencyProvider
from ..utils import get_provider_instance, update_exchange_rate_activity


def get_or_create_exchange_rate(source_currency_code, target_currency_code):
    """
    Retrieves the latest exchange rate between the source and target currencies.
    If the exchange rate is not available in the database, it attempts to fetch it
    from an active currency provider. The rate is then saved in the database.

    Args:
        source_currency_code (str): The code of the source currency.
        target_currency_code (str): The code of the target currency.

    Returns:
        Decimal or None: The exchange rate if found or fetched successfully, otherwise None.
    """
    source_currency = Currency.objects.get(code=source_currency_code)
    target_currency = Currency.objects.get(code=target_currency_code)

    exchange_rate = CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency.code,
        target_currency__code=target_currency.code,
        active=True,
        valuation_date=now().date(),
    ).first()

    if exchange_rate:
        return exchange_rate.rate_value

    providers = CurrencyProvider.objects.filter(active=True).order_by("priority")

    for provider in providers:
        try:
            provider_instance = get_provider_instance(provider, provider.url)
            provider_instance.set_url(provider.url, EndpointType.LATEST.value)
            data = provider_instance.get_exchange_rate_data(
                source_currency.code, target_currency.code, ""
            )
            if data and data.get("rates", []):
                rates = data.get("rates", [])
                rate_value = rates[target_currency.code]
                if rate_value:
                    update_exchange_rate_activity(
                        source_currency,
                        target_currency,
                        rate_value,
                        datetime.now(),
                        provider,
                    )
                    return round(Decimal(rate_value), 3)

        except Exception as e:
            logging.error(f"Error fetching from provider {provider.name}: {e}")
            continue

    return None
