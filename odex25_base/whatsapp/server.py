import logging
from odoo.service.server import CommonServer

_logger = logging.getLogger(__name__)

class ExtendedCommonServer(CommonServer):
    _on_stop_funcs = []
    @classmethod
    def on_stop(cls, func):
        """ Register a cleanup function to be executed when the server stops """
        cls._on_stop_funcs.append(func)

    def stop(self):
        for func in self._on_stop_funcs:
            try:
                _logger.debug("on_close call %s", func)
                func()
            except Exception:
                _logger.warning("Exception in %s", func.__name__, exc_info=True)

