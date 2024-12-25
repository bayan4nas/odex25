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


class kpi_period(models.Model):
    _inherit = "kpi.period"

    def name_get(self):
        return super(models.Model, self).name_get()

    def action_export_scorecard(self):
        """
        The method to prepare the xls table

        Methods:
         * _get_xls_table of kpi.scorecard.line

        Returns:
         * action of downloading the xlsx table

        Extra info:
         * Expected singleton
        """
        self.ensure_one()
        if not xlsxwriter:
            raise UserError(_("The Python library xlsxwriter is installed. Contact your system administrator"))
        file_name = u"{}.xlsx".format(self.name_get()[0][1])
        file_path = tempfile.mktemp(suffix='.xlsx')
        workbook = xlsxwriter.Workbook(file_path)
        main_header_style = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': 'silver',
            'border_color': 'gray',
        })
        main_cell_style_dict = {
            'font_size': 11,
            'border': 1,
            'border_color': 'gray',
        }
        worksheet = workbook.add_worksheet(file_name)
        column_keys = [
            {"key": "A", "label": _("KPI Code"), "width": 14},
            {"key": "B", "label": _("KPI"), "width": 60},
            {"key": "C", "label": _("Target"), "width": 14},
            {"key": "D", "label": _("Success"), "width": 14},
            {"key": "E", "label": _("Actual"), "width": 14},
            {"key": "F", "label": _("Progress"), "width": 14},
            {"key": "G", "label": _("Weight"), "width": 14},
            {"key": "H", "label": _("Weight progress"), "width": 14},
            {"key": "I", "label": _("Notes"), "width": 80},
        ]
        total_row_number = len(self.line_ids)
        cell_values = self.line_ids._get_xls_table()
        for ccolumn in column_keys:
            ckey = ccolumn.get("key")
            # set columns
            worksheet.set_column('{c}:{c}'.format(c=ckey), ccolumn.get("width"))
            # set header row
            worksheet.write("{}1".format(ckey), ccolumn.get("label"), main_header_style)
            # set column values
            for row_number in range(2, total_row_number + 2):
                cell_number = "{}{}".format(ckey, row_number)
                cell_value_dict = cell_values.get(cell_number)
                cell_value = ""
                cell_level = 0
                cell_style = main_cell_style_dict.copy()
                if cell_value_dict:
                    cell_value = cell_value_dict.get("value")
                    cell_style.update(cell_value_dict.get("style"))
                    cell_level = cell_value_dict.get("level") or 0
                cell_style = workbook.add_format(cell_style)
                if ckey == "A":
                    cell_style.set_indent(cell_level)
                worksheet.write(
                    cell_number,
                    cell_value,
                    cell_style,
                )
        worksheet.set_row(0, 24)
        workbook.close()
        with open(file_path, 'rb') as r:
            xls_file = base64.b64encode(r.read())
        att_vals = {
            'name': file_name,
            'type': 'binary',
            'datas': xls_file,
        }
        attachment_id = self.env['ir.attachment'].create(att_vals)
        self.env.cr.commit()
        action = {
            'type': 'ir.actions.act_url',
            'url': '/web/content/{}?download=true'.format(attachment_id.id, ),
            'target': 'self',
        }
        return action

