import glob
import os
import django
import csv
import json
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyCurrency.settings')
django.setup()

from MyCurrencyApp.models import Currency, CurrencyProvider, CurrencyExchangeRate

def run_migrations():
    """Run Django migrations."""
    os.system('python manage.py migrate')

def add_currencies():
    """Add currency objects to the database."""
    currencies = [
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'CHF', 'name': 'Swiss Franc', 'symbol': 'CHF'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
    ]

    for currency_data in currencies:
        Currency.objects.get_or_create(
            code=currency_data['code'],
            defaults={
                'name': currency_data['name'],
                'symbol': currency_data['symbol'],
            },
        )

def add_providers():
    """Add currency providers to the database."""
    providers = [
        {'name': 'Mock', 'url': 'http://mock.url', 'priority': 0, "key":""},
        {'name': 'Fixer', 'url': 'https://data.fixer.io/api/', 'priority': 1, "key":os.environ.get("FIXER_API_KEY","")},
    ]

    for provider_data in providers:
        CurrencyProvider.objects.get_or_create(
            name=provider_data['name'],
            defaults={
                'url': provider_data['url'],
                'priority': provider_data['priority'],
                'active': True,
                'default_base_currency':"EUR",
            },
            api_key=provider_data['key'],
        )

def add_exchange_rates_from_file(file_path):
    """Populate exchange rate data from a CSV or JSON file."""
    file_extension = os.path.splitext(file_path)[-1].lower()

    if file_extension == '.csv':
        with open(file_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            exchange_rate_data = list(reader)
    elif file_extension == '.json':
        with open(file_path, 'r') as json_file:
            exchange_rate_data = json.load(json_file)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    for row in exchange_rate_data:
        try:
            source_currency = Currency.objects.get(code=row['source_currency_code'])
            target_currency = Currency.objects.get(code=row['target_currency_code'])
            provider = CurrencyProvider.objects.get(name='Mock')

            exchange_rate, created = CurrencyExchangeRate.objects.get_or_create(
                source_currency=source_currency,
                target_currency=target_currency,
                valuation_date=datetime.strptime(row['valuation_date'], '%Y-%m-%d').date(),
                provider=provider,
                defaults={'rate_value': Decimal(row['rate_value']), 'active': True},
            )

        except Exception as e:
            print(f"Error adding exchange rate for {row}: {e}")

def setup():
    run_migrations()
    add_currencies()
    add_providers()

    file_patterns = ['*.csv', '*.json']
    all_files = []
    for pattern in file_patterns:
        all_files.extend(glob.glob(os.path.join("mock_data", pattern)))

    for file_path in all_files:
        add_exchange_rates_from_file(file_path)
        print(f"Loaded exchange rates from {file_path}")

if __name__ == '__main__':
    setup()
