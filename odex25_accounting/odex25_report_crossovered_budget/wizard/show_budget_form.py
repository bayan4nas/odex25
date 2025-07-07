from odoo import models, fields, api,_
import io
import xlsxwriter
import base64
from collections import defaultdict
from datetime import datetime, date
import datetime

class BudgetSelectionWizard(models.TransientModel):
    _name = 'budget.selection.wizard'
    _description = 'Budget Selection Wizard'

    budget_ids = fields.Many2many(
        'crossovered.budget',
        string="Select Budgets",
        required=True
    )
    date_from = fields.Date('Start Date', required=True, default=fields.Date.today())
    date_to = fields.Date('End Date', required=True, default=fields.Date.today())

    def _compute_confirm_for_order_lines(self, order_lines):
        result = []
        for ol in order_lines:
            orders_without_tax = ol.price_subtotal
            need_tax = 0
            invoice_amount = 0

            vals = ol._prepare_compute_all_values()
            taxes = ol.taxes_id.filtered(lambda x: x.analytic).compute_all(
                vals['price_unit'], vals['currency_id'], vals['product_qty'], vals['product'], vals['partner']
            )
            need_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))

            invoiced = self.env['account.move.line'].search([
                ('purchase_line_id', '=', ol.id),
                ('move_id.state', 'not in', ['draft', 'cancel'])
            ])
            if not need_tax:
                invoice_amount += sum(invoiced.mapped('price_subtotal'))
            else:
                invoice_amount += sum(invoiced.mapped('price_total'))

            remaining = ((orders_without_tax + need_tax) - invoice_amount) * -1
            result.append({
                'order_line': ol,
                'order_name': ol.order_id.name,
                'remaining': remaining,
            })
        return result

    def action_show_budget(self):
        results = []
        for budget in self.budget_ids:
            budget_lines_data = []

            for line in budget.crossovered_budget_line:

                domain = [
                    ('confirmation_id.state', '=', 'done'),
                    ('confirmation_id.request_id.state', '!=', 'done'),
                    ('confirmation_id.request_id.purchase_create', '!=', True),
                    ('confirmation_id.type', '=', 'purchase.request'),
                    ('confirmation_id.date', '>=', self.date_from),
                    ('confirmation_id.date', '<=', self.date_to),
                    ('account_id', 'in', line.general_budget_id.account_ids.ids),
                    ('analytic_account_id', '=', line.analytic_account_id.id),
                ]
                all_lines = self.env['budget.confirmation.line'].search(domain)
                matched = all_lines

                po_line_domain = [
                    ('account_analytic_id', '=', line.analytic_account_id.id),
                    ('order_id.date_order', '>=', self.date_from),
                    ('order_id.date_order', '<=', self.date_to),
                    '|',
                    ('product_id.property_account_expense_id', 'in', line.general_budget_id.account_ids.ids),
                    ('product_id.categ_id.property_account_expense_categ_id', 'in',
                     line.general_budget_id.account_ids.ids),
                    ('order_id.state', 'in', ['draft', 'sent',  'to approve']),
                ]

                reserved_po_lines = self.env['purchase.order.line'].search(po_line_domain)


                practical_records = []
                acc_ids = line.general_budget_id.account_ids.ids
                date_to = self.date_to
                date_from = self.date_from

                if line.analytic_account_id.id:
                    domain = [
                        ('account_id', '=', line.analytic_account_id.id),
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                    ]
                    if acc_ids:
                        domain += [('general_account_id', 'in', acc_ids)]

                    practical_records = self.env['account.analytic.line'].search(domain)
                else:
                    domain = [
                        ('account_id', 'in', acc_ids),
                        ('date', '>=', date_from),
                        ('date', '<=', date_to),
                    ]
                    practical_records = self.env['account.move.line'].search(domain)
                grouped_practical_records = {}
                for record in practical_records:
                    account_name = record.account_id.name  # حساب السجل
                    if account_name not in grouped_practical_records:
                        grouped_practical_records[account_name] = []
                    grouped_practical_records[account_name].append(record)

                po_confirm_domain = [
                    ('account_analytic_id', '=', line.analytic_account_id.id),
                    ('order_id.date_order', '>=', self.date_from),
                    ('order_id.date_order', '<=', self.date_to),
                    '|',
                    ('product_id.property_account_expense_id', 'in', line.general_budget_id.account_ids.ids),
                    ('product_id.categ_id.property_account_expense_categ_id', 'in',
                     line.general_budget_id.account_ids.ids),
                    ('order_id.state', 'in', ['purchase', 'done']),
                ]
                confirm_po_lines = self.env['purchase.order.line'].search(po_confirm_domain)
                po_confirm_data = self._compute_confirm_for_order_lines(confirm_po_lines)





                budget_lines_data.append({
                    'line_name': line.name,
                    'planned_amount': line.planned_amount,
                    'initial_engagement_records': matched,
                    'provide':line.provide,
                    'pull_out':line.pull_out,
                    'remain':line.remain,
                    'reserved_po_lines': reserved_po_lines,
                    'final_amount':line.final_amount,
                    'analytic_account': line.analytic_account_id.name or '',
                    'practical_records': practical_records,
                    'po_confirm_data':po_confirm_data

                })


            results.append({
                'crossovered_name': budget.name,
                'budget_lines': budget_lines_data,
            })
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet("Budget Report")

        center_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': True
        })
        header_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'bg_color': '#eeeeee',
            'bold': True
        })

        # header = [
        #     "الباب", "بند الموازنة", "الحساب التحليلي", "الحساب",
        #     "تاريخ", "رقم الطلب", "المبلغ المخطط", "تعزيز",
        #     "تخفيض", "قيمة الموازنة النهائي", "الربط المبدئي", "المبلغ المحجوز",
        #     "المبلغ التعميد", "المبلغ الفعلي", "المبلغ المتبقي"
        # ]
        header = [
            _("Budgets"),  # الباب
            _("Budget Line"),  # بند الموازنة
            _("Analytic Account"),  # الحساب التحليلي
            _("Account"),  # الحساب
            _("Date"),  # التاريخ
            _("Order Number"),  # رقم الطلب
            _("Planned Amount"),  # المبلغ المخطط
            _("Provide"),  # تعزيز
            _("Pull Out"),  # تخفيض
            _("Final Budget Value"),  # قيمة الموازنة النهائي
            _("Initial Engagement"),  # الربط المبدئي
            _("Reserved Amount"),  # المبلغ المحجوز
            _("Confirmed Amount"),  # المبلغ التعميد
            _("Practical Amount"),  # المبلغ الفعلي
            _("Remaining Budget"),  # المبلغ المتبقي
        ]

        report_title = f"تقرير الموازنة للفترة من {self.date_from.strftime('%Y/%m/%d')} إلى {self.date_to.strftime('%Y/%m/%d')}"
        sheet.write(0, 1, report_title, header_format)
        sheet.set_row(0, 40)
        max_widths = [len(str(h)) for h in header]

        for col, name in enumerate(header):
            sheet.write(3, col, name, header_format)

        row = 4
        current_analytic_account = None
        line_total = 0
        for budget in results:
            for line in budget['budget_lines']:
                for rec in line['initial_engagement_records']:

                    if line['analytic_account'] != current_analytic_account:
                        current_analytic_account = line['analytic_account']
                        line_total = 0

                    amount = abs(rec.amount)

                    line_total += amount
                    total_spent = (abs(line['final_amount']) - line_total) * -1

                    values = [
                        budget['crossovered_name'], line['line_name'], line['analytic_account'],
                        rec.account_id.name or '',
                        str(rec.confirmation_id.date), rec.confirmation_id.name, line['planned_amount'],
                        line['provide'], line['pull_out'], line['final_amount'],
                        rec.amount, 0, 0,0, total_spent
                    ]
                    for col, val in enumerate(values):
                        sheet.write(row, col, val, center_format)
                        max_widths[col] = max(max_widths[col], len(str(val)))
                    sheet.set_row(row, 30)
                    row += 1

                for po in line['reserved_po_lines']:
                    account_name = (
                            po.product_id.property_account_expense_id.name or
                            po.product_id.categ_id.property_account_expense_categ_id.name or ''
                    )
                    date_order = po.order_id.date_order
                    formatted_date = date_order.strftime('%Y-%m-%d') if isinstance(date_order, (datetime.date, datetime.datetime)) else str(date_order)
                    if line['analytic_account'] != current_analytic_account:
                        current_analytic_account = line['analytic_account']
                        line_total = 0
                    line_total += abs(po.price_total)
                    total_spent = (abs(line['final_amount']) - line_total) * -1

                    values = [
                        budget['crossovered_name'], line['line_name'], line['analytic_account'], account_name,
                        formatted_date, po.order_id.name, line['planned_amount'],
                        line['provide'], line['pull_out'], line['final_amount'],
                        0, po.price_total, 0,0, total_spent
                    ]
                    for col, val in enumerate(values):
                        sheet.write(row, col, val, center_format)
                        max_widths[col] = max(max_widths[col], len(str(val)))
                    sheet.set_row(row, 30)
                    row += 1

                for po_data in line['po_confirm_data']:
                    po = po_data['order_line']
                    account_name = (
                            po.product_id.property_account_expense_id.name or
                            po.product_id.categ_id.property_account_expense_categ_id.name or ''
                    )
                    date_order = po.order_id.date_order.strftime('%Y-%m-%d') if po.order_id.date_order else ''
                    if line['analytic_account'] != current_analytic_account:
                        current_analytic_account = line['analytic_account']
                        line_total = 0
                    line_total += abs(po_data['remaining'])
                    total_spent = (abs(line['final_amount']) - line_total) * -1
                    values = [
                        budget['crossovered_name'], line['line_name'], line['analytic_account'], account_name,
                        date_order, po_data['order_name'], line['planned_amount'],
                        line['provide'], line['pull_out'], line['final_amount'],
                        0, 0,po_data['remaining'], 0, total_spent
                    ]
                    for col, val in enumerate(values):
                        sheet.write(row, col, val, center_format)
                        max_widths[col] = max(max_widths[col], len(str(val)))
                    sheet.set_row(row, 30)
                    row += 1

                grouped_practical_records = defaultdict(list)
                for rec in line['practical_records']:
                    account_name = rec.general_account_id.name if hasattr(rec,
                                                                          'general_account_id') else rec.account_id.name
                    grouped_practical_records[account_name or 'غير محدد'].append(rec)

                for account_name, records in grouped_practical_records.items():
                    for rec in records:
                        amount = rec.amount if hasattr(rec, 'amount') else rec.credit - rec.debit
                        date = getattr(rec, 'date', '')
                        order_number = ''
                        if hasattr(rec, 'move_id') and rec.move_id:
                            order_number = rec.name or ''
                        elif hasattr(rec, 'name'):
                            order_number = rec.name or ''
                        if line['analytic_account'] != current_analytic_account:
                            current_analytic_account = line['analytic_account']
                            line_total = 0
                        line_total += abs(amount)
                        total_spent = (abs(line['final_amount']) - line_total) * -1

                        values = [
                            budget['crossovered_name'], line['line_name'], line['analytic_account'], account_name,
                            str(date), order_number, line['planned_amount'],
                            line['provide'], line['pull_out'], line['final_amount'],
                            0, 0,0, amount, total_spent
                        ]
                        for col, val in enumerate(values):
                            sheet.write(row, col, val, center_format)
                            max_widths[col] = max(max_widths[col], len(str(val)))
                        sheet.set_row(row, 30)
                        row += 1
                if not line['initial_engagement_records'] and not line['reserved_po_lines'] and not line[
                    'po_confirm_data'] and not line['practical_records']:
                    values = [
                        budget['crossovered_name'], line['line_name'], line['analytic_account'], '',
                        '', '', line['planned_amount'],
                        line['provide'], line['pull_out'], line['final_amount'],
                        0, 0, 0, 0, line['remain']
                    ]
                    for col, val in enumerate(values):
                        sheet.write(row, col, val, center_format)
                        max_widths[col] = max(max_widths[col], len(str(val)))
                    sheet.set_row(row, 30)
                    row += 1

        for col, width in enumerate(max_widths):
            sheet.set_column(col, col, width)


        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.read())
        filename = 'budget_report.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': file_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}
