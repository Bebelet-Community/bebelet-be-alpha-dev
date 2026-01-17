# core/exceptions.py
from rest_framework.exceptions import APIException, Throttled
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from core.responses import build_response


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)


    if response is None:
        return response

    if isinstance(exc, Throttled):
        wait = getattr(exc, "wait", None)

        message = "Too many requests."
        if wait:
            message = f"Too many requests. Try again in {wait} seconds."

        return Response(
            build_response(
                success=False,
                code=status.HTTP_429_TOO_MANY_REQUESTS,
                message=message,
            ),
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )


    if isinstance(exc, APIException):
        detail = exc.detail
        if isinstance(detail, (list, dict)):
            message = "Validation error"
        else:
            message = str(detail)

        return Response(
            build_response(
                success=False,
                code=response.status_code,
                message=message,
                data=response.data if isinstance(response.data, dict) else {},
            ),
            status=response.status_code,
        )

    return response
