from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class EmployeePurchaseReportRequistionWizard(models.TransientModel):
    _name = 'employee.purchase.requistion'
    _description = 'Purchase Requistion Report'

    type = fields.Selection([('total' , 'Total') , ('detailed' , 'Detailed')])
    vendor_ids = fields.Many2many(comodel_name='res.partner', string='Vendor')
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employee')
    department_ids = fields.Many2many(comodel_name='hr.department', string='Deparments')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    product_ids = fields.Many2many(comodel_name='product.product', string='Products')
    state = fields.Selection(
        [('draft', 'Draft'), ('direct_manager', 'Technical Department'),('dm', 'Managment manager'),('ceo_purchase','Manager OF Purchasing And Contract'),
         ('general_supervisor', 'Chief Executive Officer'), ('executive_vice', 'Executive Vice President'),('send_budget', 'Send to Budget Confirmation'), ('wait_budget', 'Wait Budget'),
         ('budget_approve', 'Budget Approved'), ('waiting', 'Procurement Department'),
         ('done', 'Done'),('refuse', 'Refuse')],tracking=True, )
    # def state_value(self):
    #     value=''
    #     if self.state=='draft':
    #         value='Draft'
    #     elif self.state=='in_progress':
    #         value = 'Confirmed'
    #
    #     elif self.state=='committee':
    #         value = 'Committee'
    #     elif self.state=='purchase_manager':
    #         value = 'Purchase Manager'
    #     elif self.state=='second_approve':
    #         value = 'Second Approval'
    #     elif self.state=='third_approve':
    #         value = 'Third Approval'
    #     elif self.state=='accept':
    #         value = 'Accepted'
    #     elif self.state=='open':
    #         value = 'Bid Selection'
    #     elif self.state=='waiting':
    #         value = 'Waiting For Budget Confirmation'
    #     elif self.state=='checked':
    #         value = 'Budget Checked'
    #     elif self.state=='done':
    #         value = 'Done'
    #     elif self.state=='approve':
    #         value = 'Approved'
    #     elif self.state=='cancel':
    #         value = 'Cancelled'
    #     return v
    
    def action_print(self):
        data = {'date_from': self.date_from,'state': self.state, 'date_to': self.date_to, 'department_ids': self.department_ids.ids, 'employee_ids': self.employee_ids.ids,'type'  : self.type }
        print('print action in ....')
        return self.env.ref('purchase_custom_report.action_employee_purchase_report2').report_action([] , data = data)

class PurchaseRequReportParser(models.AbstractModel):
    _name = "report.purchase_custom_report.employee_purchase_report2"



    def _get_report_values(self, docids, data=None):

        domain = []
        if data.get('date_from'):
            domain.append(('date', '>=', data.get('date_from')))
            po_ids = self.env['purchase.request'].search(domain)
            print('p from= ,',po_ids)

        if data.get('date_to'):
            domain.append(('date', '<=', data.get('date_to')))
            po_ids = self.env['purchase.request'].search(domain)
            print('p to= ,',po_ids)
        if data.get('department_ids'):
            print('drt')
            domain.append(('id', 'in', data.get('department_ids')))
            po_ids = self.env['purchase.request'].search(domain)
            print('pdpt = ,',po_ids)
        if data.get('employee_ids'):
            print('emp =')
            domain.append(('id', 'in', data.get('employee_ids')))
            po_ids = self.env['purchase.request'].search(domain)
            print('pemp = ,',po_ids)
        if data.get('state') and data.get('type') == 'detailed':
            print('st',data.get('state'))
            domain.append(('state', '=', data.get('state')))
            po_ids = self.env['purchase.request'].search(domain)
            print('ps = ,',po_ids)
        po_ids = self.env['purchase.request'].search(domain)
        department_ids = self.env['hr.department'].browse(data.get('department_ids'))
        employee_ids = self.env['hr.employee'].browse(data.get('employee_ids'))
        data.update({'employees': ",".join([employee.name for employee in employee_ids])})
        data.update({'departments': ",".join([department.name for department in department_ids])})
        print('po = ',po_ids)
        report_values = []
        deparments = []
        product_ids = data.get('product_ids')
        if len(po_ids) == 0:
            raise ValidationError(_("There is no Data"))

        return {
            'doc_ids': po_ids.ids,
            'doc_model': 'purchase.request',
            'docs': po_ids,
            'datas': data,
        }

    def date_format(self,date):
        strdate = str(date)
        if type(strdate) == str:
            return datetime.strptime(strdate, "%Y-%m-%d %H:%M:%S").date()

    def _get_total_products(self,po_ids,product_ids):
        po_ids = str(po_ids).replace('[' , '(')
        po_ids = str(po_ids).replace(']' , ')')
        product_ids = str(product_ids).replace('[' , '(')
        product_ids = str(product_ids).replace(']' , ')')

        self.env.cr.execute("""
                            SELECT 
                                sum(line.qty) qty, 
                                product_templ.name product_name,
                                sum(line.sum_total) product_price 
                            FROM 
                                purchase_request_line line 
                            left join 
                                product_product product on (line.product_id = product.id) 
                            left join  
                                product_template product_templ on (product.product_tmpl_id = product_templ.id) 
                            where line.request_id in """ + po_ids +""" and 
                                line.product_id in """+ product_ids+"""
                            group by product_templ.name;
                        """)
        products = self.env.cr.dictfetchall()
        return products

    def _get_po_lines(self,po_ids,product_ids):
        lines = self.env['purchase.request.line'].search([('request_id' , 'in' , po_ids),('product_id' , 'in' , product_ids)])
        return lines

        
    

