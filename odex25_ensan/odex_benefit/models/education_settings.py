from odoo import fields, models,api


class EducationEntities(models.Model):
    _name = 'education.entities'

    name = fields.Char(string='Name')

class EducationLevel(models.Model):
    _name = 'education.level'

    name = fields.Char(string='Name')

class EducationClassroom(models.Model):
    _name = 'education.classroom'

    name = fields.Char(string='Name')
class EducationResults(models.Model):
    _name = 'education.result'

    name = fields.Char(string='Name',compute="get_name")
    evaluation = fields.Char(string='Evaluation')
    min_degree = fields.Float(string='Mini Degree')
    max_degree = fields.Float(string='Max Degree')

    @api.depends("evaluation","min_degree","max_degree")
    def get_name(self):
        for rec in self:
            if rec.evaluation and rec.max_degree and rec.min_degree:
                rec.name = rec.evaluation + " " + str(rec.min_degree) + "-" + str(rec.max_degree)
            else:
                rec.name=""
class StudyMaterial(models.Model):
    _name = 'study.material'

    name = fields.Char(string='Name')
