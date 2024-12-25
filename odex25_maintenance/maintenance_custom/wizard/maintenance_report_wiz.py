from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import  ValidationError

def to_str(array):
    return ",".join(str(i) for i in array)


class MaintenanceReportWiz(models.TransientModel):
    _name = 'maintenance.report.wiz'

    time_from = fields.Datetime('From', required=True)
    time_to = fields.Datetime('To', required=True)
    equipment_ids = fields.Many2many('maintenance.equipment', 'equipment_report_wiz_rel' , string='Equipment')
    category_ids = fields.Many2many('maintenance.equipment.category', 'equipment_cat_report_wiz_rel', string='Equipment Category' )
    spare_categ_ids = fields.Many2many('product.category', 'spare_cat_report_wiz_rel', string='Spare Category' )
    failure_ids = fields.Many2many('maintenance.failure', 'failure_report_wiz_rel' , string='Failure Type')
    user_ids = fields.Many2many('res.users', 'users_report_wiz_rel' , string='Supervisor')
    department_ids = fields.Many2many('hr.department', 'dep_report_wiz_rel' , string='Department')
    employee_ids = fields.Many2many('hr.employee', 'emp_report_wiz_rel' , string='Members')
    team_type = fields.Selection([('in', 'Internal Team'), ('out', 'Outsite Entity')], string='Team Type')
    spare_ids = fields.Many2many('product.template', 'spare_report_wiz_rel' , string='Spare Parts', domain=[('is_spare','=',True)])
    machine_status = fields.Selection([('out_service', 'Out of Service'),('part','Partially effect'),('in_service','In Service')], string='Machine Status')
    report_type = fields.Selection([
        ('general', 'General Report'),
        ('spare','Spare Parts'),
        ('equipment', 'Equipment'),
        ('team','Team Members')], string='Report Type')

    def _filters(self):
        cond = []
        filters = {}
        if self.time_from :
            cond.append(['request_date', '>=' , self.time_from])
        if self.time_to :
            cond.append(['request_date', '<=' , self.time_to])
        if self.equipment_ids :
            cond.append(['equipment_id', 'in' , self.equipment_ids.ids])
            stri = ",".join(i.name for i in  self.equipment_ids)
            filters.update({'equipment_id' :stri})
        if self.category_ids:
            equipment_ids = self.env.get('maintenance.equipment').search([('category_id', 'in',self.category_ids.ids )])
            cond.append(['equipment_id', 'in' , equipment_ids.ids])
            stri = ",".join(i.name for i in  self.category_ids)
            filters.update({'category_id' :stri})
        if self.user_ids :
            cond.append(['user_id', 'in' , self.user_ids.ids])
            stri = ",".join(i.name for i in  self.user_ids)
            filters.update({'user_id' :stri})
        if self.failure_ids :
            cond.append(['failure_id', 'in' , self.failure_ids.ids])
            stri = " , ".join(i.name for i in  self.failure_ids)
            filters.update({'failure_id' :stri})
        if self.team_type :
            cond.append(['team_type', '=' , self.team_type])
            stri = self.team_type == 'in' and 'Internal Team' or 'Outsite Entity'
            filters.update({'team_type' :stri})
        if self.machine_status :
            cond.append(['machine_status', '=' , self.machine_status])
            stri = self.team_type
            filters.update({'machine_status' :stri})
        if self.spare_ids or self.report_type == 'spare' :
            ids = self.spare_ids and self.spare_ids.ids or self.env.get('product.template').search([('is_spare', '=', True)]).ids
            spare_ids = self.env.get('maintenance.request.spare').search([('spare_id', 'in',ids )])
            order_ids = [s.request_id.id for s in spare_ids]
            cond.append(['id', 'in' , order_ids])
            stri = " , ".join(i.name for i in  self.spare_ids)
            filters.update({'spare_id' :stri})
        if self.department_ids or self.employee_ids  or self.report_type == 'team' :
            emp_cond = []
            if self.department_ids : 
                emp_cond += [('department_id', 'in', self.department_ids.ids)]
                dep_stri = " , ".join(i.name for i in  self.department_ids)
                filters.update({'department_id' :dep_stri})
            emp_ids = self.employee_ids.ids and self.employee_ids.ids or self.env.get('hr.employee').search(emp_cond).ids
            emp_ids_str = " , ".join(str(i) for i in  emp_ids)
            query = '''
                select maintenance_request_id from req_member_rel where hr_employee_id in (%s)
            '''%(emp_ids_str)
            self.env.cr.execute(query)
            res = self.env.cr.fetchall()
            order_ids = [r[0] for r in res]
            cond.append(['id', 'in' , order_ids])
            stri = " , ".join(i.name for i in  self.env['hr.employee'].browse(emp_ids))
            filters.update({'employee_id' :stri})
        if self.spare_categ_ids:
            product_ids = self.env.get('product.template').search([('categ_id', 'in',self.spare_categ_ids.ids ),('is_spare', '=', True)])
            spare_ids = self.env.get('maintenance.request.spare').search([('spare_id', 'in',product_ids.ids )])
            order_ids = [s.request_id.id for s in spare_ids]
            cond.append(['id', 'in' , order_ids])
            stri = " , ".join(i.name for i in  self.spare_categ_ids)
            filters.update({'spare_categ_id' :stri})
        return cond , filters

    def print_report(self):
        cond , filters = self._filters()
        requests =  self.env.get('maintenance.request').search(cond)
        if not requests : 
            raise ValidationError(_('Connot Find any Request/Order .')) 
        time_from = self.time_from
        time_to = self.time_to
        totals = self.compute_general_report(requests)
        data = {
            'form' : {
                'time_from' : time_from,
                'time_to' : time_to,
                'total' : totals,
                'filters' : filters,
                'rec_ids' : requests.ids + [0],
                'spare_categ_ids' : self.spare_categ_ids.ids,
                'spare_ids' : self.spare_ids.ids,
                'category_ids' : self.category_ids.ids,
                'equipment_ids' : self.equipment_ids.ids,
                'employee_ids' : self.employee_ids.ids,
                'department_ids' : self.department_ids.ids,
                },
        }
        if self.report_type == 'general':
            report = self.env.ref('maintenance_custom.action_general_maintenance_report').report_action(requests,data=data)
        elif self.report_type == 'spare':
            report = self.env.ref('maintenance_custom.action_spare_part_report').report_action(requests,data=data)
        if self.report_type == 'equipment':
            report = self.env.ref('maintenance_custom.action_equipment_report').report_action(requests,data=data)
        if self.report_type == 'team':
            report = self.env.ref('maintenance_custom.action_maintenance_team_report').report_action(requests,data=data)
        return report

    

    def _get_total_members(self, order_str):
        query = '''
            SELECT
                 count(distinct hr_employee_id ) 
                 FROM req_member_rel WHERE maintenance_request_id IN (%s)

        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total


    def _get_total_equipment(self, order_str):
        query = '''
             SELECT count(distinct equipment_id) 
             FROM maintenance_request WHERE id IN (%s)
        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total

    
    def _get_total_cost(self, order_str):
        query = '''
             SELECT sum(quantity * cost) FROM maintenance_request_spare WHERE request_id IN (%s)
        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total


    def _get_total_downtime(self, order_str):
        query = '''
             SELECT sum(down_time) 
             FROM maintenance_request WHERE id IN (%s) and machine_status = 'out_service'
        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total


    def _get_total_loss(self, order_str):
        query = '''
             SELECT sum(product_loss) 
             FROM maintenance_request WHERE id IN (%s) and machine_status = 'part'
        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total
    

    def _get_total_over_due(self, order_str):
        query = '''
            SELECT count(id) FROM maintenance_request 
            WHERE duration > 0 AND done_time >= schedule_date + interval '1' HOUR * duration 
            AND id in (%s) and stage_id in (select id from maintenance_stage where stage_type = 'request_done' )
        '''%(order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0] 
        except :
            total = 0
        return total


    def _get_total_planned(self, order_ids):
        count = self.env.get('maintenance.request').search_count([
                            ('id', 'in', order_ids),
                            ('maintenance_category','=', 'planned')
                            ])
        return count


    def _get_high_priority(self, order_ids):
        count = self.env.get('maintenance.request').search_count([
                            ('id', 'in', order_ids),
                            ('priority','=', '3')
                            ])
        return count

    
    def _get_total_closed(self, order_ids):
        res = self.env.get('maintenance.stage').search([('stage_type', '=', 'request_done')])
        stage_done = res.ids
        count = self.env.get('maintenance.request').search_count([
                            ('id', 'in', order_ids),
                            ('stage_id','in', stage_done),
                            ])
        return count


    def _get_total_open(self,order_ids):
        res = self.env.get('maintenance.stage').search([('stage_type', '!=', 'request_done')])
        stage_open = res.ids
        count = self.env.get('maintenance.request').search_count([
                            ('id', 'in', order_ids),
                            ('stage_id','in', stage_open),
                            ])
        return count        

    def _get_total_working_hours(self,order_str):
        res = self.env.get('maintenance.stage').search([('done', '=', True)])
        stage_done = res.ids
        query = '''
            SELECT sum(EXTRACT(EPOCH FROM done_time-start_time)/3600) FROM maintenance_request
            WHERE Stage_id in (%s) and id in (%s)
        '''%(to_str(stage_done), order_str)
        self.env.cr.execute(query)
        try :
            total =  self.env.cr.fetchall()[0][0]
            total = round(total,2)
        except :
            total = 0
        return total


    def compute_general_report(self, orders):
        order_ids = orders.ids
        order_str = ",".join(str(i) for i in order_ids)
        total_orders = len(order_ids)
        planned =  round((self._get_total_planned(order_ids) / float(total_orders) * 100 ), 2)
        overdue = self._get_total_over_due(order_str)
        over_due_percentage = overdue / total_orders * 100
        over_due_percentage = round(over_due_percentage, 2)
        res = {
            'total_equipment' : self._get_total_equipment(order_str),
            'total_members' : self._get_total_members(order_str),
            'total_orders' : total_orders ,
            'total_over_due' : overdue,
            'over_due_percentage' : over_due_percentage ,
            'total_planned' : planned,
            'total_high' : self._get_high_priority(order_ids),
            'total_loss' : self._get_total_loss(order_str),
            'total_downtime' : self._get_total_downtime(order_str),
            'total_colse' : self._get_total_closed(order_ids),
            'total_open' : self._get_total_open(order_ids),
            'total_working_hours' : self._get_total_working_hours(order_str),
            'total_cost' : self._get_total_cost(order_str),
        }
        return res
    