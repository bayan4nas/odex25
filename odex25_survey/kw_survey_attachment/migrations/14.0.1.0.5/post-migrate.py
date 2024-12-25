import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    user_input_line_ids = env['survey.user_input.line'].search([])
    for il in user_input_line_ids:
        if il.value_file:
            il.write({
                'value_file_ids': [(6, 0, [il.value_file.id])]})
