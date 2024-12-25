# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """ Inherit the res. partner to make existing field required. """
    _inherit = 'res.partner'

    # image_1920 = fields.Image(max_width=1920, max_height=1920,
    #                           required=True, string="Image",
    #                           help="The field hold the image of customer")
    # phone = fields.Char(unaccent=False, required=True,
    #                     string="Phone",
    #                     help="The field hold the phone number of customer")
    # function = fields.Char(string='Job Position',
    #                        help="The field hold the job position  of customer")

    def server_action_get_card(self):
        """ Used to fetch data from res. partner to pass in template"""
        partner_id = self.env['res.partner'] \
            .browse(self.env.context.get('active_ids'))
        company_id = self.env.company
        if self.is_member:
            data = {
                'name': partner_id.name,
                'product_id': partner_id.product_id.name,
                'membrship_level':partner_id.membrship_level.name,
                'membrship_level_color':partner_id.membrship_level.color,
                'membrship_no':partner_id.membrship_no,
                'image': partner_id.image_1920,
                'start_date': partner_id.join_date,
                'end_date': partner_id.memebership_end_date,
                'company_name': company_id.name,
            }
            return self.env.ref('membership_card_odoo.action_membership'
                                '_card').report_action(None, data=data)
        raise ValidationError(
            'Need to buy membership inorder to print membership card')
