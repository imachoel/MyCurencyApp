# MY CURRENCY APP #

## Setup Guide
### 1. Set up Database ###
[PostgreSQL Setup Instructions](instructions/POSTGRES_SETUP.md)
### 2. Create an .env ###
Create a `.env` file in the root directory of your project and add the following environment variables:

```ini
# Debug mode
DEBUG=True

# Database configuration
DB_PASSWORD=<your_database_password>
DB_USERNAME=<your_database_username>
DB_NAME=<your_database_name>

# Other environment variables
FIXER_API_KEY=<your_fixer_api_key>
```
### 3. Build Virtual Environment ###
Run the following command to build venv:
```bash
python -m venv .venv
```
Start Virtual Environment on Linux
```bash
source .venv/bin/activate
```
Start Virtual Environment on Windows

```bash
.venv\Scripts\activate.bat
```

Install the Requirements
```bash
pip install -r requirements.txt
```
 
### 4. Run the Setup Script

To complete the setup, run the provided Python setup script:

```bash
python setup.py
```
### 4. Start the App
```bash
python manage.py runserver
```
## API Documentation

###  1. Currency Converter API
- **Endpoint**: /api/currency-converter/

- **Description**: Converts an amount from one currency to another using the latest exchange rate. If the currency or exchange rate is not found in the database, the system will attempt to fetch it from a provider.

- **Method**: GET

- **Parameters**:
  - `source_currency` (str): The currency code to convert from.
  - `target_currency` (str): The currency code to convert to.
  - `amount` (float): The amount to be converted.

- **Response**:
  - Success (200): Returns the converted amount along with the exchange rate used.
    ```
    {
        "source_currency": "USD",
        "target_currency": "EUR",
        "exchange_rate": 0.85,
        "amount": 100.00,
        "converted_amount": 85.00
    }
    ```
    - Error (400): Returns an error message for missing parameters, unsupported currencies, or invalid amount.
    - Error (404): Exchange rate not found.
    - Error (500): Server error.

### 2. Currency Rates List API
- **Endpoint**: /api/currency-rates/

- **Description**: Retrieves a list of currency exchange rates for a specified time period, either from the database or active providers.

- **Method**: GET

- **Parameters**:

  - `source_currency (str)`: The base currency code.
  - `date_from (str)`: Start date of the period in YYYY-MM-DD format.
  - `date_to (str)`: End date of the period in YYYY-MM-DD format.

- **Response**:

  - **Success (200)**: Returns a dictionary with date keys and exchange rate values.

    ```
    {
    "CHF": [
        {
            "rate_value": 1.116767,
            "valuation_date": "2024-09-01"
        },
        {
            "rate_value": 1.118897,
            "valuation_date": "2024-09-02"
        },
    ],
    "EUR": [
        {
            "rate_value": 1.188606,
            "valuation_date": "2024-09-01"
        },
        {
            "rate_value": 1.187417,
            "valuation_date": "2024-09-02"
        },
    ],
    "USD": [
        {
            "rate_value": 1.312767,
            "valuation_date": "2024-09-01"
        },
        {
            "rate_value": 1.31414,
            "valuation_date": "2024-09-02"
        },
    ]
}
    ```

 - **Error (400)**: Returns an error message for missing parameters or unsupported currencies.
 - **Error (404)**: No exchange rates found for the given period.
 - **Error (500)**: Server error.

### 3. Currency TWRR API

- **Endpoint**: /api/currency-twrr/

- **Description**: Calculates the Time-Weighted Rate of Return (TWRR) for an investment in a given currency over a specified period.

- **Method**: GET

- **Parameters**:

  - `source_currency` (str): The currency code for the initial investment.
  - `exchanged_currency` (str): The currency code to which the investment is converted.
  - `amount` (float): The amount invested.
  - `start_date` (str): The start date of the investment period in YYYY-MM-DD format.

- **Response**:

 - **Success (200)**: Returns a time series of TWRR values.
   ```
     {
     "source_currency": "CHF",
     "exchanged_currency": "GBP",
     "amount_invested": 250.0,
     "start_date": "2024-09-08",
     "twrr_series": [
         {
             "valuation_date": "2024-09-08",
             "rate_value": 0.902263,
             "twrr": 0,
             "amount": 225.56575
         },
         {
             "valuation_date": "2024-09-08",
             "rate_value": 1.139027,
             "twrr": 0.2624112924945387,
             "amount": 284.75675
         },
     ]
    }
   ```

 - **Error (400)**: Returns an error message for missing parameters, unsupported currencies, or invalid amount format.
 - **Error (404)**: No historical exchange rates found.
 - **Error (500)**: Server error.

## Admin Access

In the Django admin interface, you can access the following views:

1. **Currency Converter**: 
   - **URL**: `/admin/mycurrencyapp/currency/currency-converter/`
   - **Description**: Use this view to convert amounts between different currencies using the latest exchange rates.

2. **Exchange Rate Graph**: 
   - **URL**: `/admin/mycurrencyapp/currencyexchangerate/exchange-rate-graph/`
   - **Description**: This view provides a graphical representation of exchange rate trends over time for different currencies.
      Before accessing this view, please set the Mock provider priority to 0 (set the Mock provider as the default provider)


## GitHub Workflows
### 1. GitHub Workflow: on Pull Request
GitHub workflow to automate the testing process. The workflow is configured to run tests automatically whenever a pull request (PR) is opened to the `master` branch. This ensures that all code changes are tested before being merged, helping maintain code quality and stability.

The workflow includes the following steps:
- Setting up a Python environment.
- Creating a virtual environment.
- Installing the project dependencies from `requirements.txt`.
- Running the test suite.

You can find the workflow configuration file in the `.github/workflows/` directory of the repository.
