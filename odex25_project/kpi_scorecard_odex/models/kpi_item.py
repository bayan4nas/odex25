# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2024 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class kpi_item(models.Model):

    _inherit = "kpi.item"

    code = fields.Char(string="KPI Code", required=True)
    weight = fields.Float(string="Weight")
    automated_weight = fields.Boolean(string="Automated Weight", default=True)
    kpi_domain = fields.Selection([
        ("university", "University Strategy"), 
        ("research", "Scientific Research"),
        ("institute", "Institutional Accreditation"),
        ("program", "Program Accreditation")], string="KPI Domain", required=True, default="university")     
    program_id = fields.Many2one("kpi.category", string="Program")
    kpi_type = fields.Selection([
        ("efficiency", "Efficiency"), 
        ("effectiveness", "Effectiveness"),
        ("productivity", "Productivity"),
        ("financial", "Financial"),
        ("quality", "Quality"),
        ("security", "Security")], string="KPI Type", required=True, default="efficiency")  
    kpi_type_region = fields.Selection([
        ("inputs", "Inputs"), 
        ("processes", "Processes"),
        ("outputs", "Outputs"),], string="KPI Type By Region", required=True, default="inputs") 
    data_source = fields.Selection([
        ("achievement", "Achievement"), 
        ("direct_data", "Direct Data"),
        ("poll", "Opinion Polls"),], string="Data source", required=True, default="achievement") 
    measurement_method = fields.Selection([
        ("data_entry", "Data entry"), 
        ("integration", "integration"),], string="Measurement Method", required=True, default="data_entry") 
    measurement_periodic= fields.Selection([
        ("periodical", "Periodical"), 
        ("annually", "Annually"),], string="Measurement Periodicity", required=True, default="annually") 
    kpi_owner_id = fields.Many2one("res.partner", string="KPI Owner")
    internal_bench_ids = fields.Many2many("res.partner",  
        "res_partner_kpi_item_rel_internal", 
        "res_partner_id", "kpi_item_id", string="Internal Benchmarking")
    external_bench_ids = fields.Many2many("res.partner",  
        "res_partner_kpi_item_rel_external", 
        "res_partner_id", "kpi_item_id",  string="External Benchmarking")
        
    kpi_period = fields.Selection([
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),("5", "5") ], string="KPI Period", default="5")
        
    line_ids = fields.One2many("kpi.scorecard.line", "kpi_id", string="KPI Targets", copy=True)
    
    
    def compute_automated_weight(self, category_ids):
        for category in category_ids:
            goal_kpis = self.env["kpi.item"].sudo().search([ ("category_id", "=", category.id),("automated_weight", "=", True)])
            goal_kpis_edit = self.env["kpi.item"].sudo().search([ ("category_id", "=", category.id),("automated_weight", "=", False)])
            goal_weight = category.weight - sum(goal_kpis_edit.mapped('weight')) 
            if len(goal_kpis) > 0:
                weight = round(goal_weight / len(goal_kpis) , 2)
                goal_kpis.write({"weight": weight})
                
    @api.model
    def create(self, data):
        res = super(kpi_item, self).create(data)
        category_ids =[]
        for kpi in res:
            category_ids.append(kpi.category_id)
        self.compute_automated_weight(category_ids)
        return res
            
    def write(self, data):
        category_ids =[]
        for kpi in self:
           if data.get('category_id'):
               category_ids.append(kpi.category_id)
        res = super(kpi_item, self).write(data)
        if data.keys() & {'automated_weight', 'active', 'category_id'}:
            for kpi in self:
                category_ids.append(kpi.category_id)
        if data.get('weight') and not data.get('automated_weight'):
            for kpi in self:
                if not kpi.automated_weight:
                    category_ids.append(kpi.category_id) 
        self.compute_automated_weight(category_ids)
        return res

    def unlink(self):
        category_ids =[]
        for kpi in self:
           category_ids.append(kpi.category_id)
        res = super(kpi_item, self).unlink()
        self.compute_automated_weight(category_ids)
        return res
                   
    @api.onchange('category_id')
    def onchange_category_id(self):
        '''
        This function generates the kpi code automatically with the possibility to modify it
        '''
        if self.category_id and self.category_id.code:
            parent_code = self.category_id.code
            count = len (self.search([("category_id", "=", self.category_id.id)])) or 1 
            serial = int(count)
            added = 0
            code = ''
            while True:
                serial += added
                code_length = len(str(parent_code)) + len(str(serial))
                code = parent_code +str(serial)
                if not self.search([('code','=',code)]):
                    break
                added += 1
            self.code = code  
                
                
                
                
