from odoo import fields, models, _

class ChangePartner(models.TransientModel):
    _name = 'update.partner'
    _description = 'Create partner regestration'
    partner_ids = fields.Many2many(
        string='partner',
        comodel_name='res.partner'
    )
    
    def update_state(self):
        for partner in self.partner_ids:
            registration_ids = self.env["firebase.registration"].search(
                [("partner_id", "in", [partner.id])]
            )
            if not registration_ids:
                self.env['firebase.registration'].create({
                    "partner_id": partner.id
                })