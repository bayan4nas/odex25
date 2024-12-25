from bs4 import BeautifulSoup
from odoo import models, fields, api, _

class YourModel(models.Model):
    _inherit = 'mail.template'

    def ag_remove_powered_by_odoo(self):
        powered_by = "<!-- POWERED BY -->"
        for record in self:
            if powered_by in str(record.body_html):
                body_html = record.body_html
                soup = BeautifulSoup(body_html, 'html.parser')
                powered_element = soup.find('td', attrs={'style': 'text-align: center; font-size: 13px;'})

                if powered_element:
                    powered_element['style'] = 'text-align: center; font-size: 13px; display: none !important;'
                    record.write({'body_html': str(soup)})
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'success',
                            'sticky': True,
                            'message': _('Templates have been cleaned up successfully'),
                            'next': {
                                'type': 'ir.actions.client',
                                'tag': 'reload'
                            }
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'sticky': True,
                        'params': {
                            'type': 'warning',
                            'message': _('Powered by Odoo not found in the template'),
                        }
                    }
