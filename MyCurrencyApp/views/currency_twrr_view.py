import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..enums.available_currencies import AvailableCurrencies
from ..helper.get_twrr_series import calculate_twrr


class CurrencyTWRRView(APIView):
    """
    API endpoint to calculate Time-Weighted Rate of Return (TWRR) for any given amount
    invested from a source currency into an exchanged currency from a start date until today.

    Parameters:
    - source_currency (str): The currency you are converting from.
    - amount (float): The amount invested in the source currency.
    - exchanged_currency (str): The currency you are converting to.
    - start_date (str): The start date of the investment in format YYYY-MM-DD.

    Expected response: A time series list of TWRR values for each available historical exchange rate.
    """

    def get(self, request):
        source_currency_code = request.query_params.get("source_currency")
        exchanged_currency_code = request.query_params.get("exchanged_currency")
        amount = request.query_params.get("amount")
        start_date = request.query_params.get("start_date")

        if not all([source_currency_code, exchanged_currency_code, amount, start_date]):
            return Response(
                {"error": "Missing required parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            source_currency_code not in AvailableCurrencies.CURRENCIES
            and exchanged_currency_code not in AvailableCurrencies.CURRENCIES
        ):
            return Response(
                {"error": "Currencies not supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {"error": "Amount must be greater than zero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Retrieve historical rates and calculate TWRR
            twrr_series = calculate_twrr(
                source_currency_code, exchanged_currency_code, amount, start_date
            )

            if not twrr_series:
                return Response(
                    {
                        "error": "No historical exchange rates available for the given parameters"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "source_currency": source_currency_code,
                    "exchanged_currency": exchanged_currency_code,
                    "amount_invested": amount,
                    "start_date": start_date,
                    "twrr_series": twrr_series,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logging.error(f"Error calculating TWRR: {e}")
            return Response(
                {"error": "An error occurred while calculating TWRR"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
