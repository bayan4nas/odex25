from odoo import fields, models, api, _


class KPIitem(models.Model):
    _inherit = 'kpi.item'

    department_item_id = fields.Many2one(comodel_name='hr.department', string='Department',domain="[('department_type', '=', 'department')]")
    responsible_item_id = fields.Many2one(comodel_name='hr.employee', string='Responsible')
    job_id = fields.Many2one('hr.job', string='Job Title')
    
    method_of_calculate = fields.Selection(string='Method Of Calculate',
                                           selection=[('accumulative', 'Accumulative'), ('avrerage', 'Average'),
                                                      ('undefined', 'Undefined')], required=False,
                                           default='accumulative')
    result_type = fields.Selection(
        [
            ("more", "Ascending"),
            ("less", "Descending"),
            ("fixed", "Within scope"),
        ],
        string="Success Criteria",
        default="more",
        required=True,
    )
    result_appearance = fields.Selection(
        [
            ("number", "# Number"),
            ("percentage", "% Percentage"),
            ("monetory", "$ cost"),
        ],
        string="Result Type",
        default="number",
        required=True,
    )
    result_rounding = fields.Selection(
        [
            ("1", "Monthly"),
            ("2", "Quarterly"),
            ("3", "Semi-Annual"),
            ("4", "Annual"),
        ],
        string="Rounding Decimals",
        default="2",
        required=True,
    )

    @api.onchange('department_item_id')
    def onchange_responsible(self):
        domain = []
        if self.department_item_id:
            domain = [('department_id', '=', self.department_item_id.id)]
        return {'domain': {'responsible_item_id': domain}}
