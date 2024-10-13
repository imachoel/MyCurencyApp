import logging
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..enums.available_currencies import AvailableCurrencies

from ..helper.get_create_exchange_rate import get_or_create_exchange_rate


class CurrencyConverterView(APIView):
    """
    API endpoint to convert an amount from one currency to another based on the latest exchange rate.
    If a currency doesn't exist in the database, it will be added.
    If an exchange rate doesn't exist, it will be fetched from a provider and added to the database.
    """

    def get(self, request):
        source_currency_code = request.query_params.get("source_currency")
        target_currency_code = request.query_params.get("target_currency")
        amount = request.query_params.get("amount")

        if not all([source_currency_code, target_currency_code, amount]):
            return Response(
                {"error": "Missing required parameters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
                source_currency_code not in AvailableCurrencies().list
                or target_currency_code not in AvailableCurrencies().list
        ):
            return Response(
                {"error": "Currencies not supported"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if float(amount) <= 0:
                return Response(
                    {"error": "Amount must be greater than zero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValueError:
            return Response(
                {"error": "Invalid amount format"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            amount = Decimal(amount)
            exchange_rate = get_or_create_exchange_rate(
                source_currency_code, target_currency_code
            )

            if not exchange_rate:
                return Response(
                    {"error": "Exchange rate not available"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            converted_amount = amount * exchange_rate

            return Response(
                {
                    "source_currency": source_currency_code,
                    "target_currency": target_currency_code,
                    "exchange_rate": exchange_rate,
                    "amount": amount,
                    "converted_amount": converted_amount,
                },
                status=status.HTTP_200_OK,
            )

        except ValueError:
            logging.error("Invalid amount")
            return Response(
                {"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logging.error(e)
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
