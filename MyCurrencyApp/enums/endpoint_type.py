from enum import Enum


class EndpointType(Enum):
    """
    Enum to define the types of API endpoints for retrieving exchange rates.
    """

    LATEST = "latest"
