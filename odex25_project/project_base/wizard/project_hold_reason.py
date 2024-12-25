from odoo import fields, models,_


class ProjectHoldWizard(models.TransientModel):

    _name = "project.hold.wizard"

    reason_id = fields.Many2one("project.hold.reason", string="Reason", required=True)
    reason = fields.Text(string="Reason")

    def hold_project(self):
        self.ensure_one()
        act_close = {"type": "ir.actions.act_window_close"}
        project_ids = self._context.get("active_ids")
        if project_ids is None:
            return act_close
        project = self.env["project.project"].browse(project_ids)
        
        msg1 = _('Project Hold for %s',self.reason_id.name)
        msg2 = " "
        if self.reason:
            msg2 = _(' with Reason: %s',self.reason)
        msg = msg1 + msg2
        project.hold_reason = self.reason
        project.action_hold()
        project.message_post(body=msg)
        return act_close
