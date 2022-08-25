from rest_framework.views import exception_handler


def default_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None and "detail" in response.data:
        response.data["message"] = response.data["detail"]

    return response
