# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


def to_str(array):
    return ",".join(str(i) for i in array)


class GeneralMaintenanceReport(models.AbstractModel):
    _name = 'report.maintenance_custom.general_maintenance_report'
    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('maintenance_custom.general_maintenance_report')
        rec_ids = data['form']['rec_ids']
        docs = self.env.get(report.model).search([('id' , 'in', rec_ids)])
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        docargs.update(data['form'])
        return docargs


class SparePartReport(models.AbstractModel):
    _name = 'report.maintenance_custom.spare_part_report'

    def _get_spare_data(self,order_ids,spare_ids,spare_categ_ids):
        cond = ""
        if spare_ids:
            cond += " AND spare_id in (%s)"%(to_str(spare_ids),)
        if spare_categ_ids:
            cond += " AND categ_id in (%s)"%(to_str(spare_categ_ids),)
        query = '''
            select 
                spare_id as spare_id ,p.name as name, count(request_id) as order_count , 
                sum(down_time) as down_time , sum(product_loss) as loss, sum(quantity * cost) as cost,
                sum(quantity) as consume , cat.name as category
            from maintenance_request_spare sp
            join maintenance_request req on sp.request_id = req.id
            join product_template p on p.id = spare_id
            join product_category cat on cat.id = p.categ_id
            where request_id in (%s) %s
            group by spare_id, p.id, cat.id
        '''%(to_str(order_ids),cond)
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        spare_model = self.env.get('product.template')
        for rec in res:
            sn = spare_model.browse(rec['spare_id']).barcode or '-'
            qty = spare_model.browse(rec['spare_id']).qty_available
            rec.update({'sn' : sn , 'stock' : qty})
        return res 

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('maintenance_custom.spare_part_report')
        rec_ids = data['form']['rec_ids']
        spare_categ_ids = data['form']['spare_categ_ids']
        spare_ids = data['form']['spare_ids']
        docs = self._get_spare_data(rec_ids,spare_ids,spare_categ_ids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        docargs.update(data['form'])
        return docargs

class EquipmentReport(models.AbstractModel):
    _name = 'report.maintenance_custom.equipment_report'

    def _get_data(self,order_ids,equipment_ids=None,category_ids=None):
        cond = ""
        if equipment_ids:
            cond += " AND eq.id in (%s)"%(to_str(equipment_ids),)
        if category_ids:
            cond += " AND categ.id in (%s)"%(to_str(category_ids),)
        order_str = ','.join(str(i) for i in order_ids)
        query = '''
            SELECT 
                eq.id as equipment_id , eq.name , vendor_partner.name as vendor , op_partner.name as opreater , categ.name as category,
                sum(req.down_time) as down_time , sum(req.product_loss) as loss,
                count(corrective.id) as corrective, count(preventive.id) as preventive
            FROM maintenance_equipment eq
            LEFT JOIN res_partner vendor_partner on vendor_partner.id = eq.partner_id
            LEFT JOIN res_users users on technician_user_id = users.id
            LEFT JOIN res_partner op_partner on users.partner_id = op_partner.id
            LEFT JOIN maintenance_equipment_category categ on categ.id = eq.category_id
            LEFT JOIN maintenance_request req on req.equipment_id = eq.id and req.id in (%s)
            LEFT JOIN maintenance_request preventive on preventive.id = req.id and preventive.maintenance_type = 'preventive'
            LEFT JOIN maintenance_request corrective on corrective.id = req.id and corrective.maintenance_type = 'corrective'
            WHERE 1 = 1 %s
            GROUP BY eq.id , vendor_partner.id, op_partner.id , categ.id 
        '''%(order_str,cond)
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        done_stage = self.env.get('maintenance.stage').search([('stage_type', '=', 'request_done')])
        done_ids = done_stage.ids
        order_model = self.env.get('maintenance.request')
        machine_status_dict = dict(
            out_service='Out of Service',
            part='Partially effect',
            in_service='In Service'
        )
        for rec in res:
            equipment_id = rec['equipment_id']
            order_res = order_model.search([('equipment_id','=',equipment_id),('stage_id', 'not in', done_ids)],order='request_date')
            machine_status = order_res and order_res[-1].machine_status or '-'
            cost = 0
            equ_order_res = order_model.search([('equipment_id','=',equipment_id),('id', 'in', order_ids)]).ids
            order_spares = self.env.get('maintenance.request.spare').search([('request_id', 'in', equ_order_res)])
            for line in order_spares:
                cost += line.quantity * line.cost
            rec.update({'machine_status' : machine_status_dict.get(machine_status, '-') , 'cost' : cost})
        return res 

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('maintenance_custom.spare_part_report')
        rec_ids = data['form']['rec_ids']
        category_ids = data['form']['category_ids']
        equipment_ids = data['form']['equipment_ids']
        docs = self._get_data(rec_ids,equipment_ids,category_ids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        docargs.update(data['form'])
        return docargs

class TeamReport(models.AbstractModel):
    _name = 'report.maintenance_custom.maintenance_team_report'

    def _get_data(self,order_ids,employee_ids=None,department_ids=None):
        cond = ""
        if employee_ids:
            cond += " AND emp.id in (%s)"%(to_str(employee_ids),)
        if department_ids:
            cond += " AND dep.id in (%s)"%(to_str(department_ids),)
        query = '''
            SELECT emp.name as name , job.name as job , dep.name as department, 
                count(on_time.id) as on_time, count(over_due.id) as over_due,
                sum(EXTRACT(EPOCH FROM work_hours.done_time-work_hours.start_time)/3600) as work_hours,
                count(closed.id) as closed , count(opened.id) as opened 
                FROM hr_employee emp
                LEFT JOIN req_member_rel rel on rel.hr_employee_id = emp.id and rel.maintenance_request_id in (%s)
                LEFT JOIN hr_department dep on dep.id = emp.department_id
                LEFT JOIN hr_job job on job.id = emp.job_id
                LEFT JOIN maintenance_request on_time on on_time.id = rel.maintenance_request_id 
                    AND on_time.duration > 0 AND on_time.done_time <= on_time.schedule_date + interval '1' HOUR * on_time.duration
                LEFT JOIN maintenance_request over_due on over_due.id = rel.maintenance_request_id 
                    AND over_due.duration > 0 AND over_due.done_time > over_due.schedule_date + interval '1' HOUR * over_due.duration    
                LEFT JOIN maintenance_request work_hours on work_hours.id = rel.maintenance_request_id 
                LEFT JOIN maintenance_request opened on opened.id = rel.maintenance_request_id and opened.stage_id  not in (select id from maintenance_stage where stage_type = 'request_done' )
                LEFT JOIN maintenance_request closed on closed.id = rel.maintenance_request_id and closed.stage_id  in (select id from maintenance_stage where stage_type = 'request_done' )
                WHERE 1 = 1 %s
            group by emp.id, job.id , dep.id
        '''%(to_str(order_ids),cond)
        self.env.cr.execute(query)
        res = self.env.cr.dictfetchall()
        for rec in res:
            if rec.get('work_hours'):
                rec.update({
                    'work_hours' : round(rec['work_hours'] , 2),
                    })
        return res 

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('maintenance_custom.maintenance_team_report')
        rec_ids = data['form']['rec_ids']
        employee_ids = data['form']['employee_ids']
        department_ids = data['form']['department_ids']
        docs = self._get_data(rec_ids,employee_ids,department_ids)
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': docs,
        }
        docargs.update(data['form'])
        return docargs