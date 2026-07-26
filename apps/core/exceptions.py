from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns a consistent error response format:
    {
        "success": false,
        "message": "Error message",
        "errors": { ... }   (optional, for validation errors)
    }
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = {
            'success': False,
            'message': _get_error_message(response.data),
        }

        # Include field-level errors for validation failures
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            error_data['errors'] = response.data

        response.data = error_data

    else:
        # Unhandled exception — log and return 500
        logger.exception(f'Unhandled exception in {context.get("view")}: {exc}')
        response = Response(
            {
                'success': False,
                'message': 'Terjadi kesalahan pada server. Silakan hubungi administrator.',
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response


def _get_error_message(data):
    """Extract a human-readable error message from DRF error data."""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                return _get_error_message(item)
    if isinstance(data, dict):
        # Try 'detail' key first (DRF standard)
        if 'detail' in data:
            detail = data['detail']
            return str(detail) if hasattr(detail, '__str__') else detail
        # Otherwise take first field's first error
        for key, value in data.items():
            msg = _get_error_message(value)
            if msg:
                return f'{key}: {msg}'
    return 'Terjadi kesalahan.'
