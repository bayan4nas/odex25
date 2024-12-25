from odoo import fields, models,api,_
from odoo.exceptions import UserError, ValidationError


class EditProjectPhase(models.TransientModel):

    _name = "edit.project.phase"

    phase_id = fields.Many2one("project.phase", string="Phase", readonly=False)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    estimated_hours = fields.Float("Additional Estimated Hours")
    edit_reasone = fields.Text("Reason")
    #TODO open in vo module
    # edit_type = fields.Selection(selection=[('vo','Variation Order'),('other','Other')],string="Edit type")
    # from_vo = fields.Boolean("From VO")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['phase_id'] = self._context.get('active_id', False)
        phase = self.env['project.phase'].browse(res['phase_id'])
        res['start_date'] = phase.start_date
        res['end_date'] = phase.end_date
        return res

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        if self.filtered(lambda c: c.end_date and c.start_date > c.end_date):
            raise ValidationError(_('Phase start date must be earlier than Phase end date.'))

    def edit_phase(self):
        self.ensure_one()
        to_write = {}
        act_close = {"type": "ir.actions.act_window_close"}
        active_id = self._context.get("active_id")
        phase = self.env['project.phase'].browse(active_id)
        if self.estimated_hours:
            estimated_hours= phase.estimated_hours + self.estimated_hours
            to_write.update({'estimated_hours':estimated_hours})
        to_write.update({'start_date':self.start_date,'end_date':self.end_date})
        phase.write(to_write)
        return act_close
