from odoo import fields, models,api,_


class EditProjectPhase(models.TransientModel):

    _inherit = "edit.project.phase"

    estimated_days = fields.Float("Additional Estimated Days")
    plan_by = fields.Selection(string='Plan By',related='phase_id.plan_by', readonly=False)

    def edit_phase(self):
        self.ensure_one()
        to_write = {}
        act_close = {"type": "ir.actions.act_window_close"}
        active_id = self._context.get("active_id")
        phase = self.env['project.phase'].browse(active_id)
        if phase.plan_by == 'man_hours':
            plan_by_hour = phase.estimated_hours + self.estimated_hours
            to_write.update({'plan_by_hour':plan_by_hour})
        elif phase.plan_by == 'man_days':
            plan_by_day = phase.plan_by_day + self.estimated_days
            to_write.update({'plan_by_day':plan_by_day})
        to_write.update({'start_date':self.start_date,'end_date':self.end_date})
        phase.write(to_write)
        return act_close
