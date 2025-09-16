import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
from django.shortcuts import redirect, render

logger = logging.getLogger(__name__)

class GlobalErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        """Catch any unhandled exception in views."""
        logger.error(
            "Unhandled exception at %s: %s",
            request.path,
            str(exception),
            exc_info=True
        )

        # Show safe red alert
        messages.error(request, f"⚠️ Something went wrong. {str(exception)}")

        # Strategy:
        # - GET → reload same page (to keep URL)
        # - POST/PUT/DELETE → fallback to home (avoid infinite loop / lost form data)
        if request.method == "GET":
            return redirect(request.path)
        else:
            return render(request, "errors/generic.html", status=500)
