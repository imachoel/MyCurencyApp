import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..enums.available_currencies import AvailableCurrencies
from ..helper.get_currency_rates import get_currency_rates_data


class CurrencyRatesListView(APIView):
    """
    API view to retrieve a list of currency rates for a specific time period.
    It fetches exchange rates either from the database or from active providers if not available.
    """

    @staticmethod
    def get(request):
        """
        Handles GET requests to retrieve currency exchange rates based on the provided parameters.

        Parameters:
            request: The HTTP request object containing query parameters.

        Returns:
            Response: A Response object containing the exchange rates or an error message.
        """
        try:
            source_currency_code = request.query_params.get("source_currency")
            date_from = request.query_params.get("date_from")
            date_to = request.query_params.get("date_to")

            if not all([source_currency_code, date_from, date_to]):
                return Response(
                    {"error": "Missing required parameters"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if source_currency_code not in AvailableCurrencies.CURRENCIES:
                return Response(
                    {"error": "Currencies not supported"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            response_data = get_currency_rates_data(
                source_currency_code, date_from, date_to
            )

            if not response_data:
                return Response(
                    {"error": "No rates found"}, status=status.HTTP_404_NOT_FOUND
                )

            response_data = {key: response_data[key] for key in sorted(response_data)}

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return Response(
                {"error": "An error occurred while processing the request."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
