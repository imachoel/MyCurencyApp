import logging
from datetime import datetime, timedelta
from .models import CurrencyExchangeRate
from .providers.fixer_provider import FixerProvider
from .providers.mock_provider import MockProvider


def is_valid_date(date_str):
    """
    Check if the provided string is in 'YYYY-MM-DD' format.

    Args:
        date_str (str): The date string to validate.

    Returns:
        bool: True if the date is valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_date_range(date_from, date_to):
    """
    Generate a list of dates between date_from and date_to, inclusive.
    Both dates should be in 'YYYY-MM-DD' format.

    Args:
        date_from (str): Start date in 'YYYY-MM-DD' format.
        date_to (str): End date in 'YYYY-MM-DD' format.

    Returns:
        list: A list of date strings in 'YYYY-MM-DD' format.
    """
    date_format = "%Y-%m-%d"
    start_date = datetime.strptime(date_from, date_format)
    end_date = datetime.strptime(date_to, date_format)

    return [
        (start_date + timedelta(days=i)).strftime(date_format)
        for i in range((end_date - start_date).days + 1)
    ]


def get_provider_instance(provider, url):
    """
    Factory method to instantiate the appropriate provider class.

    Args:
        provider (CurrencyProvider): The provider instance containing the name.
        url (str): The URL for the provider.

    Returns:
        Provider: An instance of the provider class, or None if not found.
    """
    providers = {
        "Fixer": FixerProvider,
        "Mock": MockProvider,
        # Add other providers here
    }

    provider_class = providers.get(provider.name)

    if provider_class:
        return provider_class(provider, url)
    else:
        logging.error(f"Provider name '{provider.name}' not found")
        return None


def update_exchange_rate_activity(
    source_currency, target_currency, rate_value, valuation_date, provider
):
    """
    Update the activity status of exchange rates and create a new exchange rate entry.

    Args:
        source_currency (Currency): The source currency object.
        target_currency (Currency): The target currency object.
        rate_value (Decimal): The exchange rate value.
        valuation_date (datetime): The date for the exchange rate.
        provider (CurrencyProvider): The provider of the exchange rate.

    Returns:
        CurrencyExchangeRate: The newly created or updated exchange rate entry.
    """
    CurrencyExchangeRate.objects.filter(
        source_currency__code=source_currency.code,
        target_currency__code=target_currency.code,
        valuation_date__lt=valuation_date,
    ).update(active=False)

    new_rate, _ = CurrencyExchangeRate.objects.update_or_create(
        source_currency=source_currency,
        target_currency=target_currency,
        valuation_date=valuation_date,
        defaults={
            "rate_value": rate_value,
            "provider": provider,
            "active": True,
        },
        updated_at=datetime.utcnow()
    )
    return new_rate


def format_data_for_chart(data):
    """
    Format the provided data for use in a chart.

    Args:
        data (dict): A dictionary containing source and target currencies with their rates.

    Returns:
        dict: A formatted dictionary suitable for charting.
    """
    chart_data = {"labels": [], "datasets": []}
    color_palette = [
        "rgba(75, 192, 192, 1)",
        "rgba(153, 102, 255, 1)",
        "rgba(255, 159, 64, 1)",
        "rgba(255, 99, 132, 1)",
        "rgba(54, 162, 235, 1)",
        "rgba(255, 206, 86, 1)",
        "rgba(201, 203, 207, 1)",
        "rgba(255, 99, 71, 1)",
        "rgba(75, 0, 130, 1)",
    ]

    color_index = {}

    for source_currency, target_currencies in data.items():
        if source_currency == target_currencies:
            continue
        for target_currency, rates in target_currencies.items():
            currency_pair = f"{source_currency}_{target_currency}"
            if currency_pair not in color_index:
                color_index[currency_pair] = len(color_index) % len(color_palette)

            dataset = {
                "label": f"{source_currency} to {target_currency}",
                "data": [],
                "borderColor": color_palette[color_index[currency_pair]],
                "fill": False,
            }

            for rate in rates:
                valuation_date = (
                    rate["valuation_date"].strftime("%Y-%m-%d")
                    if isinstance(rate["valuation_date"], datetime)
                    else rate["valuation_date"]
                )
                rate_value = rate["rate_value"]

                if valuation_date not in chart_data["labels"]:
                    chart_data["labels"].append(valuation_date)

                dataset["data"].append(rate_value)

            chart_data["datasets"].append(dataset)

    return chart_data
