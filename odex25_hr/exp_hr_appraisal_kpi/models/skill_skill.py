from odoo import fields, models, api
from odoo.exceptions import ValidationError



class Skill(models.Model):
    _name = 'skill.skill'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description', tracking=True)
    skill_type_id = fields.Many2one('skill.type', string='Skill Type')
    items_ids = fields.One2many('skill.item', 'skill_id', string='Items', tracking=True)

    @api.constrains('name')
    def _check_skill_name(self):
        for record in self:
            if record.name:
                existing_records = self.search([('name', '=', record.name), ('id', '!=', record.id)])
                if existing_records:
                    raise ValidationError(_('The skill name must be unique!'))


class SkillItems(models.Model):
    _name = 'skill.item'

    skill_id = fields.Many2one('skill.skill', string='Skill', ondelete='cascade')
    name = fields.Char(string='Description')
    mark = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], string='Mark')
    mark_avg = fields.Float(string='Mark')
    item_id = fields.Many2one(comodel_name='item.item',string='Item')
    display_type = fields.Selection([('line_section', "Section"),('line_note', "Note")],default=False, help="Technical field for UX purpose.")
    employee_apprisal_id = fields.Many2one(comodel_name='hr.employee.appraisal')
    sequence = fields.Integer(string='Sequence', default=10)
    level_id = fields.Many2one('skill.level', string='Skill Level')
    skill_type_id = fields.Many2one(related='skill_id.skill_type_id')
    level = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='Skill Level')


class SkillLevel(models.Model):
    _name = 'skill.level'

    name = fields.Char(string='Name')


class SkillJob(models.Model):
    _inherit = 'hr.job'

    item_job_ids = fields.Many2many('skill.item', 'merge_item_skill1_rel', 'merge1_id', 'item1_id', string='Skills')
    appraisal_percentages_id = fields.Many2one(comodel_name='job.class.apprisal',string='Appraisal Percentage')


class SkillItem(models.Model):
    _name = 'item.item'

    name = fields.Char(string='Name')


class SkillType(models.Model):
    _name = 'skill.type'

    name = fields.Char(string='Name')


