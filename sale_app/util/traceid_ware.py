import uuid
from django.utils.deprecation import MiddlewareMixin

from sale_app.util.traceId_log_handler import trace_id_var


class TraceIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        trace_id_var.set(str(uuid.uuid4()).split('-')[-1])
        return None

    def process_response(self, request, response):
        trace_id_var.set('N/A')
        return response