from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from datetime import datetime

from ..forms.converter_form import CurrencyExchangeRateForm
from ..helper.get_currency_rates import get_currency_rates_data
from ..models import Currency
from ..utils import format_data_for_chart


class ExchangeRateGraphAdmin(admin.ModelAdmin):
    """
    Custom admin interface for displaying exchange rate graphs.
    Uses a custom template to render the graph and provides additional endpoints
    for fetching exchange rate data.
    """

    change_list_template = "admin/exchange_rate_graph.html"

    def get_urls(self):
        """
        Extends the default admin URLs with custom URLs for the graph view and data fetching.

        Returns:
            list: A list of URL patterns including custom views for the exchange rate graph.
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "exchange-rate-graph/",
                self.admin_site.admin_view(self.graph_view),
                name="exchange_rate_graph",
            ),
            path(
                "exchange-rate-all-currencies/",
                self.admin_site.admin_view(self.exchange_rate_all_currencies),
                name="exchange_rate_all_currencies",
            ),
        ]
        return custom_urls + urls

    def graph_view(self, request):
        """
        Renders the HTML template for the exchange rate graph.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The rendered template with the currency exchange rate form.
        """
        form = CurrencyExchangeRateForm()
        return render(request, "admin/exchange_rate_graph.html", {"form": form})

    def exchange_rate_all_currencies(self, request):
        """
        Fetches and returns exchange rate data for all currencies based on the specified date range.

        Args:
            request (HttpRequest): The HTTP request object containing start_date and end_date parameters.

        Returns:
            JsonResponse: A JSON response with formatted exchange rate data or an error message.
        """
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid date format"}, status=400)

        source_currencies = Currency.objects.values_list("code", flat=True).distinct()
        response_data = {}

        date_format = "%Y-%m-%d"
        for source_currency in source_currencies:
            rates_data = get_currency_rates_data(
                source_currency,
                start_date.strftime(date_format),
                end_date.strftime(date_format),
            )
            response_data[source_currency] = rates_data

        formatted_data = format_data_for_chart(response_data)
        return JsonResponse({"data": formatted_data})
