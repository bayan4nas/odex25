from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class FamilyNeedCategory(models.Model):
    _name = 'family.need.category'
    _description = 'Family Need Category Classification'

    name = fields.Char(string="Family Need Category", required=True)
    min_need = fields.Float(string="Minimum Need (%)", store=True)
    max_need = fields.Float(string="Maximum Need (%)", store=True)

    @api.constrains('min_need', 'max_need')
    def _check_needs(self):
        for rec in self:
            if rec.min_need > rec.max_need:
                raise ValidationError("Minimum need cannot be greater than maximum need")

            overlapping = self.search([
                ('id', '!=', rec.id),
                ('min_need', '<=', rec.max_need),
                ('max_need', '>=', rec.min_need),
            ])
            if overlapping:
                raise ValidationError(
                    _("This need range overlaps with existing categories: %s") %
                    ', '.join(overlapping.mapped('name'))
                )
