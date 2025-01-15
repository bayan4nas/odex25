# -*- coding: utf-8 -*-
import datetime
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError


class JobTitle(models.Model):
    _name = 'cm.job.title'
    _description = 'Job Titles'

    name = fields.Char(string='Job Title')


class Entity(models.Model):
    _name = 'cm.entity'
    _description = 'Transactions Contacts'
    _order = 'name'

    
    def _normalize_arabic_text(self, text):
        translation_map = str.maketrans({
        # Define a dictionary to replace different forms of characters
            'ه': 'ة',
            'إ': 'ا',  # Replace Alef with Hamza Below with Alef
            'أ': 'ا',  # Replace Alef with Hamza Above with Alef
            'آ': 'ا',  # Replace Alef with Madda Above with Alef
            'ى': 'ي',  # Replace Alef Maqsura with Ya
            'ئ': 'ي',  # Replace Yeh with Hamza Above with Ya
            'ؤ': 'و',  # Replace Waw with Hamza Above with Waw

        })
        return text.translate(translation_map)

   
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # Normalize the search arguments for 'name' field
        new_args = []
        for arg in args:
            if isinstance(arg, (list, tuple)) and arg[0] == 'name' and arg[1] == 'ilike':
                normalized_value = self._normalize_arabic_text(arg[2])
                new_args.append('|')
                new_args.append(arg)
                new_args.append(('name', 'ilike', normalized_value))
            else:
                new_args.append(arg)
        return super(Entity, self).search(new_args, offset=offset, limit=limit, order=order, count=count)



    @api.constrains('code')
    def _check_code(self):
        count = self.search_count([('code', '=', self.code), ('id', '!=', self.id)])
        if self.code:
            if count:
                raise ValidationError(_("Validation Error Entity Code Must Be unique !"))
            if self.type == 'unit':
                x = ''
                if len(self.code) == 3 or len(self.code) == 2:
                    x = 'a'
                if self.code.isalpha() == False or x == '':
                    raise ValidationError(_("Validation Error Entity Code Must Be Composed from 3/2 characters"))

    code = fields.Char(string='Code')
    # sequence = fields.Integer(string='Sequence')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=False, ondelete='cascade',
                                 copy=False)
    name = fields.Char(string='Name', store=True)
    type = fields.Selection(string='Entity Type', selection=[('unit', _('Internal Unit')), ('employee', _('Employee')),
                                                             ('external', _('External Unit'))], default='unit')
    parent_id = fields.Many2one(comodel_name='cm.entity', string='Parent Entity')
    department_id = fields.Many2one('hr.department')
    manager_id = fields.Many2one(comodel_name='cm.entity', string='Unit Manager')
    secretary_id = fields.Many2one(comodel_name='cm.entity', string='Employee in charge of transactions')
    user_id = fields.Many2one(comodel_name='res.users', string='Related User', related='employee_id.user_id', store=True)
    # job_title_id = fields.Many2one(comodel_name='cm.job.title', string='Job Title')
    job_title_id = fields.Many2one(comodel_name='hr.job', string='Job Title')
    need_approve = fields.Boolean(string='Need Aprove')
    executive_direction = fields.Boolean(string='Executive direction')
    is_secret = fields.Boolean(string='Is Secret')
    person_id = fields.Char(string='Person ID')
    person_id_issue_date = fields.Date(string='Person ID Issue Date')
    employee_assignment_date = fields.Date(string='Employee Assignment Date')
    employee_id = fields.Many2one('hr.employee')
    phone = fields.Char()
    email = fields.Char()
    child_ids = fields.Many2many(comodel_name='cm.entity', relation='employee_entity_rel', column1='employee_id',
                                 column2='entity_id', string='Related Units')
    image = fields.Binary(string='Image')
    establish_date = fields.Date(string='Establish Date')
    unit_location = fields.Char(string='Unit Location')
    sketch_attachment_id = fields.Many2one(comodel_name='ir.attachment', string='Sketch Attachment')
    dynamic_year = fields.Char(string='Year', default=datetime.datetime.now().strftime('%Y'))
    year_increment = fields.Boolean(string='Continue Increment every year?', help='''
                Check if you want to continue incrementing in the start of every new year.
            ''', default=True)
    delegate_employee_id = fields.Many2one('cm.entity')
    from_date = fields.Datetime(string='Delegation From Date')
    to_date = fields.Datetime(string='Delegation To Date')
    to_delegate = fields.Boolean(string='To Delegate?', compute="_compute_to_delegate")

    def _compute_to_delegate(self):
        for rec in self:
            rec.to_delegate = False
            if rec.from_date and rec.to_date:
                if rec.from_date <= fields.Datetime.now() < rec.to_date:
                    rec.to_delegate = True
                else:
                    rec.to_delegate = False

    @api.onchange('department_id')
    def onchange_department_id(self):
        self.name = self.department_id.name

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.job_title_id = self.employee_id.job_id
        self.name = self.employee_id.name
        self.person_id = self.employee_id.iqama_number.iqama_id
        self.email = self.employee_id.personal_email
        self.phone = self.employee_id.mobile_phone
        self.person_id_issue_date = self.employee_id.iqama_number.expiry_date
        # self.employee_assignment_date = self.employee_id.job_id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.name = self.partner_id.name
        self.email = self.partner_id.email
        self.phone = self.partner_id.phone

    ####################################################
    # ORM Overrides methods
    ####################################################
    @api.model
    def create(self, vals):
        if vals.get('type', False) == 'employee':
            vals['partner_id'] = self.env['hr.employee'].search(
                [('id', '=', vals['employee_id'])]).user_id.partner_id.id
        if 'partner_id' not in vals:
            print("*******************")
            if vals.get('type', False) == 'employee':
                user_id = vals.get('user_id', False)
                if user_id:
                    vals['partner_id'] = self.env['res.users'].search([('id', '=', user_id)]).partner_id.id
            else:
                partner = self.env['res.partner'].create({
                    'name': vals.get('name', ''),
                    'email': vals.get('email', ''),
                    'city': vals.get('city', _('Riyadh')),
                    'is_company': vals.get('is_company', True),
                    'country_id': self.env.ref('base.sa', True).id,
                })
                vals['partner_id'] = partner.id
        sequence = {
            'employee': '01',
            'unit': '02',
            'external': '03',
        }
        if not vals.get('code', False):
            seq = self.env['ir.sequence'].get('cm.entity')
            s = u'{}-{}'.format(sequence[vals.get('type', 'employee')], seq)

            if vals.get('type') == 'employee' or vals.get('type') == 'external':
                vals['code'] = s
        return super(Entity, self).create(vals)

    def write(self, vals):
        sequence = {
            'employee': '01',
            'unit': '02',
            'external': '03',
        }
        if not vals.get('code', False):
            seq = self.env['ir.sequence'].get('cm.entity')
            s = u'{}-{}'.format(sequence[vals.get('type', 'employee')], seq)
            if vals.get('type') == 'employee' or vals.get('type') == 'external':
                vals['code'] = s
        return super(Entity, self).write(vals)

    def copy(self, default=None):
        raise UserError(_('You cannot duplicate an entity!'))


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_transaction_entity = fields.Boolean('Is Transaction Entity?')

    @api.model
    def create(self, values):
        res = super(ResPartner, self).create(values)
        if values.get('is_transaction_entity'):
            entity = self.env['cm.entity'].create({
                'name': values.get('name', ''),
                'partner_id': values.get('id'),
            })
        return res

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        if vals.get('is_transaction_entity'):
            if not self.env['cm.entity'].search([('partner_id', '=', self.id)]):
                entity = self.env['cm.entity'].create({
                    'name': self.name,
                    'partner_id': vals.get('id'),
                })
        return res
