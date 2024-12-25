# -*- coding: utf-8 -*-
{
    'name': "Odex25 Project Base",
    'summary': """Odex25 Project Base""",
    'description': """
1- Project Charter 
2- Project Stage
3- Project Tasks
4- Project Invoice Requests
    """,
    'category': 'Odex25-Project/Odex25-Project',
    'version': '1.0',
    'depends': ['sale_timesheet','hr' ,'project','mail',  'portal',  'base' ,'account','account_attachments'],
    'data': [
        'data/project_data.xml',
        'data/project_cron.xml',
        'security/project_security.xml',
        'security/ir_rule_allow_users.xml',
        'security/ir.model.access.csv',
        'wizard/project_hold_reason_view.xml',
        'wizard/edit_project_phase_view.xml',
        'wizard/down_payment_invoice_advance_views.xml',
        'report/project_reports.xml',
        'report/project_report_templates.xml',
        'report/project_invoice_report_templates.xml',
        'views/project_views.xml',
        'views/project_invoice_views.xml',
        'views/project_phase_view.xml',
        'views/res_config_setting.xml',
        'views/project_task_views.xml',
        'views/asset.xml',
        
    ],
}
