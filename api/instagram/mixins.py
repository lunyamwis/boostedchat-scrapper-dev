from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

class HybridResponseMixin:
    """
    Mixin to return either DRF Response (JSON) or Django rendered HTML template.
    """

    template_name = None
    admin_template_name = None

    def is_admin_request(self):
        return (
            self.request.path.startswith('/admin/') or
            (self.request.user.is_authenticated and self.request.user.is_staff)
        )

    def render_to_response(self, context, **response_kwargs):
        format_param = self.request.GET.get('format')
        accept = self.request.META.get('HTTP_ACCEPT', '')

        wants_html = (format_param == 'html') or ('text/html' in accept)
        is_admin = self.is_admin_request()

        if wants_html:
            if is_admin and self.admin_template_name:
                return render(self.request, self.admin_template_name, context)
            elif self.template_name:
                return render(self.request, self.template_name, context)

        return Response(context, **response_kwargs)


