# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2024 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
import base64
import logging
import tempfile

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.warning("Cannot import xlsxwriter")
    xlsxwriter = False


class kpi_scorecard_line(models.Model):
    _inherit = "kpi.scorecard.line"

    @api.depends("target_value", "actual_value", "computation_error", "kpi_id", "kpi_id.result_appearance",
                 "kpi_id.result_preffix", "kpi_id.result_suffix", "kpi_id.result_type")
    def _compute_formatted_actual_value(self):
        """
        Compute method for formatted_actual_value, result, formatted_target_value

        Methods:
         * _return_formated_appearance of kpi.item
        """
        for line in self:
            kpi_id = line.kpi_id
            company_currency = line.period_id.company_id.currency_id
            if line.computation_error:
                line.formatted_actual_value = _("N/A")
                line.result = "error"
                line.formatted_target_value = kpi_id._return_formated_appearance(
                    line.target_value, novalue_change=True, currency=company_currency,
                )
                line.formatted_planed_value = kpi_id._return_formated_appearance(
                    line.planed_value, novalue_change=True, currency=company_currency,
                )
            else:
                actual_value = line.actual_value
                line.formatted_actual_value = kpi_id._return_formated_appearance(
                    line.actual_value, novalue_change=False, currency=company_currency,
                )
                line.formatted_planed_value = kpi_id._return_formated_appearance(
                    line.planed_value, novalue_change=True, currency=company_currency,
                )
                line.formatted_target_value = kpi_id._return_formated_appearance(
                    line.target_value, novalue_change=True, currency=company_currency,
                )
                result_type = kpi_id.result_type
                actual_value = line.kpi_id.result_appearance == "percentage" and (actual_value * 100) or actual_value
                bigger_result = actual_value >= line.target_value
                if result_type == "more":
                    line.result = bigger_result and "success" or "failure"
                elif result_type == "less":
                    line.result = bigger_result and "failure" or "success"

    weight = fields.Float(string="Weight", related="kpi_id.weight", store=True)
    code = fields.Char(string="KPI Code", related="kpi_id.code", store=True)
    progress = fields.Float("Progress", compute='_compute_progress_kpi', store=True, group_operator="avg")
    weight_progress = fields.Float("Weight Progress", compute='_compute_progress_kpi', store=True, )
    target_value = fields.Float(string="Success Value")
    planed_value = fields.Float(string="Target Value")
    formatted_planed_value = fields.Char(
        string="Target",
        compute=_compute_formatted_actual_value,
        compute_sudo=True,
        store=True,
    )

    pillar_categ_id = fields.Many2one(comodel_name='kpi.category', compute='_compute_parent_category', store=True, )
    strategic_category_id = fields.Many2one(comodel_name='kpi.category', compute='_compute_parent_category',
                                            store=True, )
    plan_progress = fields.Float(string="Planned Progress", compute='_compute_progress_kpi', store=True,
                                 )

    def get_strategic_category(self, category_id):
        """
             Get the last parent category with type 'st_goal' in the chain of categories.

             :param category_id: The initial category for which to find the last 'pillar' parent.
             :return: The last Strategic Goal parent category or None if not found.
             """
        if category_id.type == 'st_goal':
            return category_id

        while category_id.parent_id:
            category_id = category_id.parent_id
            if category_id.type == 'st_goal':
                return category_id
        return None

    def get_pillar_category(self, category_id):
        """
             Get the last parent category with type 'pillar' in the chain of categories.

             :param category_id: The initial category for which to find the last 'pillar' parent.
             :return: The last 'pillar' parent category or None if not found.
             """
        if category_id.type == 'pillar':
            return category_id

        while category_id.parent_id:
            category_id = category_id.parent_id
            if category_id.type == 'pillar':
                return category_id
        return None

    def action_compare_with_partners_targets(self):
        return self.env['ir.actions.act_window']._for_xml_id('kpi_scorecard_odex.scorecard_line_tree_action')

    @api.depends('kpi_id', 'kpi_id.category_id')
    def _compute_parent_category(self):
        for line in self:
            last_pillar_categ = line.get_pillar_category(line.category_id)
            last_strategic_categ = line.get_strategic_category(line.category_id)
            line.pillar_categ_id = last_pillar_categ.id if last_strategic_categ else False
            line.strategic_category_id = last_strategic_categ.id if last_strategic_categ else False

    @api.depends('target_value', 'actual_value', 'weight')
    def _compute_progress_kpi(self):
        for kpi in self:
            if (kpi.target_value > 0.0):
                if kpi.actual_value > kpi.target_value:
                    kpi.progress = 100
                else:
                    kpi.progress = round(100.0 * kpi.actual_value / kpi.target_value, 2)
            else:
                kpi.progress = 0.0

            kpi.weight_progress = round((kpi.progress * kpi.weight) / 100.0, 2)
            kpi.plan_progress = kpi.progress * kpi.weight

    def _get_xls_table(self):
        """
        The method to prepare dict of values for xls row

        Args:
         * spaces - str - to add at the beginning of the name

        Methods:
         * _return_xls_formatting - of kpi.item
    
        Returns:
         * dict
        """
        result = {}
        row = 2
        previous_kpis = {}
        for line in self:
            parent_id = line.kpi_id.parent_id.id
            level = previous_kpis.get(parent_id) is not None and previous_kpis.get(parent_id) + 1 or 0
            previous_kpis.update({line.kpi_id.id: level})
            description = line.description or ""
            target_value = line.target_value
            planed_value = line.planed_value
            actual_value = line.actual_value
            overall_style = {
                "color": line.result == "success" and "black" or line.result == "failure" and "red" or "orange"
            }
            if line.computation_error:
                target_value = 0
                planed_value = 0
                actual_value = 0
                description = "{} {}".format(line.computation_error, description)
                overall_style.update({"color": "orange"})
            planed_value = line.kpi_id._return_xls_formatting(line.planed_value, False)
            target_value = line.kpi_id._return_xls_formatting(line.target_value, False)
            actual_value = line.kpi_id._return_xls_formatting(line.actual_value, True)
            num_style = overall_style.copy()
            num_style.update({
                "align": "center",
            })
            num_style1 = num_style.copy()

            if line.kpi_id.result_appearance == "percentage":
                num_style.update({"num_format": 10}),
            overall_style.update({
                "valign": "vjustify",
            })

            result.update({
                "A{}".format(row): {"value": line.kpi_id.code, "style": overall_style, "level": level},
                "B{}".format(row): {"value": line.kpi_id.name, "style": overall_style, "level": level},
                "C{}".format(row): {"value": planed_value, "style": num_style},
                "D{}".format(row): {"value": target_value, "style": num_style},
                "E{}".format(row): {"value": actual_value, "style": num_style},
                "F{}".format(row): {"value": line.progress, "style": num_style1},
                "G{}".format(row): {"value": line.kpi_id.weight, "style": num_style1},
                "H{}".format(row): {"value": line.weight_progress, "style": num_style1},
                "I{}".format(row): {"value": description, "style": overall_style},
            })
            row += 1
        return result

    def action_assign_target_values(self):
        self.ensure_one()
        partner_target_ids = self.env['partner.target'].search([('kbi_line_id', '=', self.id)])
        action = {
            'name': _('Targets'),
            'type': 'ir.actions.act_window',
            'res_model': 'partner.target',
            'view_mode': 'tree',
            'context': {'default_kbi_line_id': self.id},
            'target': 'current',
            'domain': [('id', 'in', partner_target_ids.ids)],
        }
        return action
