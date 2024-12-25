from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json
import base64
import urllib.parse


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'
    project_start_date = fields.Date('Project start date')
    check_chief_executive = fields.Boolean()
    chief_executive_officer = fields.Many2one('res.users', compute='get_chief_executive_officer', store=True)
    selected_supplier_id = fields.One2many('purchase.requests.line', 'purchase_line_ids')
    material_spec = fields.Selection([('yes', 'Yes'), ('no', 'NO')], string='Material Specification')
    quality_spec = fields.Selection([('yes', 'Yes'), ('no', 'NO')], string='quality Specification')
    delivery_samples = fields.Selection([('yes', 'Yes'), ('no', 'NO')], string='Delivery Samples')
    delivery_type = fields.Selection([('electronic', 'Electronic'), ('manual', 'Manual')], string='Delivery type')
    # building = fields.Char('Building')
    # floor = fields.Char('Floor')
    room = fields.Char('room/department')
    # date_time = fields.Datetime('Date&Time')
    material_notes = fields.Char(string='Note')
    quality_notes = fields.Char(string='Note')
    business_place = fields.Char(string='Business Place')
    special_condition = fields.Char(string='Special Condition')
    attachment_scope_project = fields.Char(string="Scope Project", copy=False)
    work_service_imp = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Work service Implementation')
    alternative_offer = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Allow Alternative Offer')
    # remain_budget = fields.Float(string='Remain', compute='get_remaining_budget', store=True)
    date_receive_offer = fields.Selection([('day', 'Day'), ('month', 'Month'), ('year', 'Year')],
                                          string='Proposed Period Receiving Offer')
    day = fields.Integer(string='Day')
    month = fields.Integer(string='Month')
    year = fields.Integer(string='Year')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    attachment_scop = fields.Binary(related="company_id.attachment_scop",string='Application brochure',)

    remain_budget = fields.Float(string='Remain', compute='get_remaining_budget', store=True)

    state = fields.Selection(
        selection_add=[('draft', 'Request Producer'),
                       ('dm', 'Chief Executive Officer'),
                       ('str_pro_department', 'Strategy Projects Departments'),
                       ('direct_manager', 'Technical Department'),
                       ('send_budget', 'Budget Management'),
                       ('wait_budget', 'Pending Budget Approve'),
                       ('budget_approve', 'Executive Vice President of Corporate Resources'),
                       ('general_supervisor', 'Chief Procurement Executive'),
                       ('waiting', 'Procurement Department'),
                       ('done', 'Done'),
                       ('cancel', 'Cancel'),
                       ('refuse', 'Refuse')], default="draft", tracking=True)
    purchase_type = fields.Selection(
        [('less_thirty', 'Less than thirty'), ('less_twenty', 'Less Than Twenty'), ('competitive', 'Competitive')])
    department_alter_offer = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Department Alternative Offer')
    document_list = fields.Char(string='Document List')
    record_licenses = fields.Char(string='Records and licenses')
    mech_evaluating_supp = fields.Char(string='Evaluating supplier mechanism')
    attachment_upload = fields.Char(string='Upload Application brochure')
    offer_requirements = fields.Char(string='Offer Requirements')
    competitive_type = fields.Char(string='Competitive Type')
    sell_document = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Sell Documents')
    need_to_reparation = fields.Selection([('previous', 'Previous'), ('comming', 'Comming'), ('noy_need', 'Not need')],
                                          string='Need Preparation')
    operational_construction = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Item Operational Construction')
    dep_suggestion = fields.Char(string='Department Suggestion')

    competitive_purchase_id = fields.Many2one('competitive.purchase.attachment')
    attach = fields.Binary(related='competitive_purchase_id.attachment_scop', attachment=True)

    @api.model
    def create(self, vals):
        default_purchase_type = self.env.context.get('default_purchase_type')
        if default_purchase_type == 'less_thirty':
            vals['name'] =self.env['ir.sequence'].next_by_code('purchase.seq30.sequence') or '/'
            com_attach = self.env['competitive.purchase.attachment'].search([])
            res = super(PurchaseRequest, self).create(vals)
            res['competitive_purchase_id'] = com_attach
            return res
        elif default_purchase_type=='competitive':
            print('com')
            vals['name'] =self.env['ir.sequence'].next_by_code('purchase.com.sequence') or '/'
            com_attach = self.env['competitive.purchase.attachment'].search([])
            res = super(PurchaseRequest, self).create(vals)
            res['competitive_purchase_id'] = com_attach
            return res
        else:
            res = super(PurchaseRequest, self).create(vals)
            com_attach = self.env['competitive.purchase.attachment'].search([])
            res['competitive_purchase_id'] = com_attach
            return res

    def download_url(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/web/content/competitive.purchase.attachment/%s/attachment_scop/attachment_scop.?download=true'% (self.competitive_purchase_id.id),
            "target": "new",
        }

    @api.constrains('date_receive_offer')
    def check_date_receiving_offer(self):
        config_settings = self.env['res.config.settings'].create(
            {})  # Create an empty record        print('config_day')
        config_settings.execute()  # Load the current configuration values
        for rec in self:
            if rec.date_receive_offer:
                if rec.day < config_settings.day and rec.day:
                    raise ValidationError(_("Days must be equal or greater than %s" % config_settings.day))
                if rec.month < config_settings.month and rec.month:
                    raise ValidationError(_("Months must be equal or greater than %s" % config_settings.month))
                if rec.year < config_settings.year and rec.year:
                    raise ValidationError(_("Years must be equal or greater than %s" % config_settings.year))

    def get_budget_line(self, product_account):
        budget_account = self.env['account.budget.post'].search([])
        for budget in budget_account:
            if budget.account_ids == product_account:
                return budget
    def action_confirm_button(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))
        self.write({'state': 'str_pro_department'})


    @api.depends('line_ids')
    def get_remaining_budget(self):
        for rec in self.line_ids:
            if len(self) ==1:
                if self.is_analytic:
                # fix issue singlton
                    self.ensure_one()
                    purchase_account = rec.account_id
                    product_account = rec.product_id.property_account_expense_id
                    budget_name = self.get_budget_line(product_account)
                    budget_accounts = self.env['crossovered.budget'].search([])
                    for account in budget_accounts.crossovered_budget_line:
                        if account.analytic_account_id == purchase_account and budget_name == account.general_budget_id:
                            rec.remain = account.remain
                            print(account.remain, 'account.remain')
                elif self.department_id:
                    department_account = self.department_id.analytic_account_id
                    budget_accounts = self.env['crossovered.budget'].search([])
                    for account in budget_accounts.crossovered_budget_line:
                        if account.analytic_account_id == department_account:
                            rec.remain = account.remain
                        
            elif len(self) >1:
                for  y in self:
                    if y.is_analytic:
                        purchase_account = rec.account_id
                        product_account = rec.product_id.property_account_expense_id
                        budget_name = self.get_budget_line(product_account)
                        budget_accounts = self.env['crossovered.budget'].search([])
                        for account in budget_accounts.crossovered_budget_line:
                            if account.analytic_account_id == purchase_account and budget_name == account.general_budget_id:
                                rec.remain = account.remain
                                print(account.remain, 'account.remain')
                    elif self.department_id:
                        department_account = self.department_id.analytic_account_id
                        budget_accounts = self.env['crossovered.budget'].search([])
                        for account in budget_accounts.crossovered_budget_line:
                            if account.analytic_account_id == department_account:
                                rec.remain = account.remain

    @api.depends('line_ids', 'department_id')
    def get_chief_executive_officer(self):
        for record in self:
            if record.is_analytic:
                item_executive_officer = record.line_ids.account_id.item_executive_officer.user_id
                record.chief_executive_officer = item_executive_officer
                return item_executive_officer
            else:
                item_executive_officer = record.department_id.analytic_account_id.item_executive_officer.user_id
                record.chief_executive_officer = item_executive_officer
                return item_executive_officer

    def read(self, records):
        res = super(PurchaseRequest, self).read(records)
        if self.chief_executive_officer == self.env.user:
            self.check_chief_executive = True
        else:
            self.check_chief_executive = False
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(PurchaseRequest, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=False)
        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='name']"):
            modifiers = json.loads(node.get("modifiers"))
            modifiers['readonly'] = True
            node.set("modifiers", json.dumps(modifiers))
        for node in doc.xpath("//field[@name='operational_construction']"):
            modifiers = json.loads(node.get("modifiers"))
            modifiers['readonly'] = [
                ('state', 'not in', ['str_pro_department'])]
        for node in doc.xpath("//field[@name='partner_id']"):
            modifiers = json.loads(node.get("modifiers"))
            modifiers['readonly'] = [
                ('state', 'not in', ['waiting'])]
            node.set("modifiers", json.dumps(modifiers))
        for node in doc.xpath("//field[@name='type_id']"):
            modifiers = json.loads(node.get("modifiers"))
            modifiers['readonly'] = [
                ('state', 'not in', ['waiting'])]
            node.set("modifiers", json.dumps(modifiers))
        for node in doc.xpath("//field[@name='line_ids']"):
            modifiers = json.loads(node.get("modifiers"))
            modifiers['readonly'] = [('state', '!=', 'draft')]
            node.set("modifiers", json.dumps(modifiers))
        res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def action_pc_confirm(self):
        if self.purchase_type != 'less_thirty':
            self.write({'state': 'general_supervisor'})
        else:
            self.write({'state': 'waiting'})

    def is_account_repeated(self, lines):
        accounts = set()
        for line in lines:
            account = line.account_id
            if account in accounts:
                print(accounts, 'line')
                return True
            accounts.add(account)
        print(accounts, 'accountsbjh')
        return False

    def check_budget(self):
        total = 0
        for line in self.line_ids:
            total += line.sum_total
            if not self.is_analytic:
                print(total, 'check_budget')
                print('Department Account')
                if abs(line.remain) < total:
                    raise ValidationError(
                        _("There is not enough balance to sen purchase request,"
                          "Please contact to your executive director"))
            else:
                if self.is_account_repeated(self.line_ids) == True:
                    if abs(line.remain) < total:
                        print('with repeated account')
                        raise ValidationError(
                            _("There is not enough balance to sen purchase request,"
                              "Please contact to your executive director"))
                else:
                    if abs(line.remain) < line.sum_total:
                        print('no repeated accounts')
                        raise ValidationError(
                            _("There is not enough balance for account %s to sen purchase request,"
                              "Please contact to your executive director") % line.account_id.name)

    def action_dm_confirm(self):
        res = super(PurchaseRequest, self).action_dm_confirm()
        self.check_budget()
        if self.purchase_type == 'less_twenty':
            if not self.selected_supplier_id:
                raise ValidationError(_("You have to select at least one supplier"))
        elif self.purchase_type == 'less_thirty':
            if not self.selected_supplier_id:
                raise ValidationError(_("You have to select at least one supplier"))
        elif self.purchase_type == 'competitive':
            line_len = 0
            for line in self.selected_supplier_id:
                line_len += 1
            if line_len < 5:
                raise ValidationError(_("You have to select at least Five supplier"))
        return res

    def technical_department(self):
        self.write({'state': 'direct_manager'})

    @api.constrains('line_ids')
    def check_amount_total(self):
        for line in self.line_ids:
            if self.purchase_type == 'less_thirty' and line.sum_total > 30000:
                raise ValidationError(_("Total Amount Must be less than thirty thousand"))
            elif self.purchase_type == 'less_twenty' and line.sum_total > 200000:
                raise ValidationError(_("Total Amount Must be less than two hundred thousand"))


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    remain = fields.Float(string='Remain Budget')


class PurchaseRequestsLine(models.Model):
    _name = 'purchase.requests.line'

    purchase_line_ids = fields.Many2one('purchase.request')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    supplier_email = fields.Char(string='Email', related='supplier_id.email')
    supplier_phone = fields.Char(string='Phone', related='supplier_id.phone')
