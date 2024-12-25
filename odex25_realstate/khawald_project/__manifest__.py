# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

{
    'name': "Project Management - Khawald",
    'summary': """Real Estate Project - Khawald""",
    'description': """ """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',
    'depends': ['project_management_custom', 'real_estate_marketing','odex25_web_map', 'dhx_gantt'],
    'data': [
        'data/templates.xml',
        'security/ir.model.access.csv',
        'views/khawald_project_config_views.xml',
        'views/khawald_project_view.xml',
        'views/internal_property_view.xml',
        'views/re_unit_view.xml',
        'views/project_task_view.xml',
        'views/resource_calendar_view.xml',
        'report/sub_contractor_report_template.xml',
        'report/sample_report_template.xml',
        'report/inspection_report_template.xml',
        'report/daily_report_template.xml',
        'report/report_action.xml',
    ],

    'installable': True,
    'application': False,
}
