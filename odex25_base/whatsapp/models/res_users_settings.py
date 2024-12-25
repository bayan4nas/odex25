# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo import SUPERUSER_ID

class ResUsers(models.Model):
    _inherit = 'res.users'

    def _is_internal(self):
        self.ensure_one()
        return not self.sudo().share

    def _is_superuser(self):
        self.ensure_one()
        return self.id == SUPERUSER_ID
# todo fix with js downgrade

# class ResUsersSettings(models.Model):
#     _inherit = 'res.users.settings'
#
#     is_discuss_sidebar_category_whatsapp_open = fields.Boolean(
#         string='WhatsApp Category Open', default=True,
#         help="If checked, the WhatsApp category is open in the discuss sidebar")
