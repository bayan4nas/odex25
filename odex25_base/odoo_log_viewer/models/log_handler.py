import logging
from odoo import api, models
from werkzeug._internal import _log

class MemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        # self.max_entries = max_entries
        self.entries = []

    def emit(self, record):
        if '/log_viewer/get_logs' in getattr(record, 'message', ''):
            return
        self.entries.append(self.format(record))
        # if len(self.entries) > self.max_entries:
            # self.entries.pop(0)


class LogHandlerManager(models.AbstractModel):
    _name = 'log.handler.manager'
    _description = 'Log Handler Manager'

    @api.model
    def _get_memory_handler(self):
        if not hasattr(LogHandlerManager, '_memory_handler'):
            LogHandlerManager._memory_handler = MemoryLogHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            LogHandlerManager._memory_handler.setFormatter(formatter)
            logging.getLogger().addHandler(LogHandlerManager._memory_handler)


            def custom_log(type, message, *args, **kwargs):
                if '/log_viewer/get_logs' not in message:
                    _log(type, message, *args, **kwargs)

            import werkzeug
            werkzeug._internal._log = custom_log

        return LogHandlerManager._memory_handler

    @api.model
    def _register_hook(self):
        self._get_memory_handler()

    @api.model
    def get_log_entries(self):
        return self._get_memory_handler().entries