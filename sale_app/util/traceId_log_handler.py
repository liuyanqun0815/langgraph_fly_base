import logging
import contextvars

trace_id_var = contextvars.ContextVar('trace_id', default='N/A')


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        trace_id = trace_id_var.get()
        record.trace_id = trace_id
        return True
