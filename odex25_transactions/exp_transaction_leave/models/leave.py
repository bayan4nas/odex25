# -*- coding: utf-8 -*-

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Leave(models.Model):
    _name = 'employee.leave'
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'
    _description = 'for mange transaction in employee leave'

    # name = fields.Char(string='Transaction Number')
    state = fields.Selection(selection=[('draft', 'Draft'), ('request', 'Request'), ('refuse', 'Refuse'),
                                        ('approve', 'Approved'), ('expired', 'Expired')], string='State',
                             default='draft')
    from_date = fields.Datetime(string='From Date', default=lambda self: fields.Datetime.now())
    to_date = fields.Datetime(string='To Date')
    employee_id = fields.Many2one(comodel_name='cm.entity', string='Employee',
                                  default=lambda self: self.default_employee_id(), readonly=True)
    alternative_employee_ids = fields.One2many('employee.leave.line', 'leave_id', string='Alternative Employees')
    alternative_manager_ids = fields.One2many('manager.leave.line', 'leave_id', string='Alternative Mangers')
    current_is_manager = fields.Boolean(string='Is Manager', compute="set_is_manager")
    to_delegate = fields.Boolean(string='To Delegate?', compute="_compute_to_delegate")

    def _compute_to_delegate(self):
        for rec in self:
            rec.to_delegate = False
            if rec.from_date and rec.to_date:
                if rec.from_date <= fields.Datetime.now() < rec.to_date:
                    rec.to_delegate = True
                else:
                    rec.to_delegate = False
                    if rec.state == 'approve':
                        rec.state = 'expired'
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        unit_id = self.env['cm.entity'].search([('user_id','=',self.env.uid)],limit=1).parent_id
        if self.env['cm.entity'].search([('user_id','=',self.env.uid)],limit=1).parent_id.manager_id.user_id.id == self.env.uid:
            args += [('employee_id.parent_id', '=', unit_id.id)]
        else:
            args += [('employee_id.user_id', '=', self.env.user.id)]
        return super(Leave, self).search(args, offset, limit, order, count)

    def default_employee_id(self):
        user = self.env.user
        em = self.env['cm.entity'].search([('user_id', '=', user.id)], limit=1)
        return len(em) and em or self.env['cm.entity']

    @api.constrains('employee_id')
    def constrains_leave(self):
        rec = self.env['employee.leave'].search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                                 ('from_date', '<=', self.to_date),
                                                 ('to_date', '>=', self.from_date),
                                                 ('state', 'in', ['request', 'approve'])])
        if rec:
            raise Warning(_('You can not create new leave for employee have leave in sam duration'))

    def set_is_manager(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        if self.employee_id.parent_id.manager_id.user_id == user_id:
            self.current_is_manager = True
        else:
            self.current_is_manager = False

    ####################################################
    # Business methods
    ####################################################
    def action_request(self):
        template_id = self.env.ref('exp_transaction_leave.email_template_delegation_notification2',False)

        for rec in self:
                rec.state = 'request'
                if rec.alternative_employee_ids:
                    for lin in rec.alternative_employee_ids:
                        emails = lin.employee_id.email
                        if emails:
                            body_html = f"""
                            <p>Hello {lin.employee_id.name},</p>
                            <p>You have been delegated a task.</p>
                            <p>Thank you.</p>
                        """
                            email_template = template_id.write(
                            {'email_to': emails,'body_html': body_html,})
                        template_id.with_context(lang=self.env.user.lang).send_mail(rec.id, force_send=True, raise_exception=False)
                if rec.alternative_manager_ids:
                    for lin in rec.alternative_employee_ids:
                                        emails = lin.employee_id.email
                                        if emails:
                                            body_html = f"""
                                                        <p>Hello {lin.employee_id.name},</p>
                                                        <p>You have been delegated a task.</p>
                                                        <p>Thank you.</p>
                                                    """
                                            email_template = template_id.write(
                                                {'email_to': emails,'body_html': body_html,})
                                        template_id.with_context(lang=self.env.user.lang).send_mail(rec.id, force_send=True, raise_exception=False)



    def action_refuse(self):
        for rec in self:
            rec.state = 'refuse'

    def action_approve(self):
        template_id = self.env.ref('exp_transaction_leave.email_template_delegation_accepted').id
        for rec in self:
            rec.state = 'approve'
            rec.employee_id.from_date = rec.from_date
            rec.employee_id.to_date = rec.to_date
            rec.employee_id.delegate_employee_id = rec.alternative_employee_ids.employee_id.id
            self.env['mail.template'].browse(template_id).send_mail(rec.id, force_send=True)

    def action_expired(self):
        date_now = date.today()
        leave_ids = self.env['employee.leave'].search([('to_date', '<', date_now), ('state', '=', 'approve')])
        if leave_ids:
            for leave in leave_ids:
                leave.state = 'expired'


class LeaveLine(models.Model):
    _name = 'employee.leave.line'
    _rec_name = 'employee_id'
    _description = 'for mange transaction in employee leave line'

    unit_id = fields.Many2one(comodel_name='cm.entity', string='Unit', domain=lambda self: self.onchange_leave_id())
    employee_id = fields.Many2one(comodel_name='cm.entity', string='Employee',
                                  domain=lambda self: self.onchange_unit_id())
    leave_id = fields.Many2one(comodel_name='employee.leave', string="Leave")

    @api.onchange('leave_id')
    def onchange_leave_id(self):
        domain = {}
        if self.leave_id:
            domain = {'unit_id': [('id', 'in', self.env['cm.entity'].search([('type', '=', 'employee'),
                                                                             ('employee_id', '=',
                                                                              self.leave_id.employee_id.employee_id.id)]).parent_id.ids)]}
        return {'domain': domain}

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        domain = {}
        if self.leave_id:
            domain = {'employee_id': [('id', 'in', self.env['cm.entity'].search([('type', '=', 'employee'),
                                                                                 ('parent_id', '=',
                                                                                  self.unit_id.id),
                                                                                 ('id', '!=',
                                                                                  self.leave_id.employee_id.id)]).ids)]}
        return {'domain': domain}


class MangerLeaveLine(models.Model):
    _name = 'manager.leave.line'
    _rec_name = 'employee_id'
    _description = 'for mange transaction in employee leave line'

    unit_id = fields.Many2one(comodel_name='cm.entity', string='Unit', domain=lambda self: self.onchange_leave_id())
    employee_id = fields.Many2one(comodel_name='cm.entity', string='Employee',
                                  domain=lambda self: self.onchange_unit_id())
    leave_id = fields.Many2one(comodel_name='employee.leave', string="Leave")

    @api.onchange('leave_id')
    def onchange_leave_id(self):
        domain = {}
        if self.leave_id:
            domain = {'unit_id': [('id', 'in', self.env['cm.entity'].search([('type', '=', 'unit'),
                                                                             ('manager_id', '!=', False),
                                                                             ('manager_id', '=',
                                                                              self.leave_id.employee_id.id)]).ids)]}
        return {'domain': domain}

    @api.onchange('unit_id')
    def onchange_unit_id(self):
        domain = {}
        if self.leave_id:
            domain = {'employee_id': [('id', 'in', self.env['cm.entity'].search([('type', '=', 'employee'),
                                                                                 ('parent_id', '=',
                                                                                  self.unit_id.id),
                                                                                 ('id', '!=',
                                                                                  self.leave_id.employee_id.id)]).ids)]}
        return {'domain': domain}


class Transaction(models.Model):
    _inherit = 'transaction.transaction'

    def get_employee_id(self, transaction):
        if transaction.to_ids:
            employee_id = transaction.to_ids[0].id
            unit_id = transaction.to_ids[0].parent_id.id
            if transaction.to_ids[0].type == 'unit':
                employee_id = transaction.to_ids[0].secretary_id.id
                unit_id = transaction.to_ids[0].id
            return employee_id, unit_id
        else:
            return False, False

    def get_employee_leave(self, employee_id, unit_id, transaction_date, ):
        employee_records = False
        record = self.env['employee.leave'].search([('employee_id', '=', employee_id),
                                                    ('from_date', '<=', transaction_date),
                                                    ('to_date', '>=', transaction_date),
                                                    ('state', '=', 'approve')],limit=1)
        if record:
            employee_records = self.env['employee.leave.line'].search([('leave_id', '=', record.id),
                                                                       ('unit_id', '=',
                                                                        unit_id)]).employee_id.id
        return employee_records

    
    def compute_receive_id(self):
        for rec in self:
            employee_id, unit_id = self.get_employee_id(rec)
            rec.receive_id = employee_id
            rec.receive_user_id = rec.receive_id.user_id
            employee_records = self.get_employee_leave(employee_id, unit_id, rec.transaction_date)
            if employee_records:
                rec.receive_id = employee_records
                rec.to_user_have_leave = True

    
    def compute_receive_manger_id(self):
        for rec in self:
            rec.receive_manger_id = False
            if rec.preparation_id:
                manager_id = self.get_employee_leave(rec.preparation_id.manager_id.id, rec.preparation_id.id,
                                                     rec.transaction_date)
                if manager_id:
                    rec.receive_manger_id = manager_id
                else:
                    rec.receive_manger_id = rec.preparation_id.manager_id
                    # rec.to_manager_have_leave = True

    def compute_have_leave(self):
        for rec in self:
            employee_id, unit_id = self.get_employee_id(rec)
            employee_records = self.get_employee_leave(employee_id, unit_id, rec.transaction_date)
            if employee_records:
                rec.to_user_have_leave = True
            else:
                rec.to_user_have_leave = False
