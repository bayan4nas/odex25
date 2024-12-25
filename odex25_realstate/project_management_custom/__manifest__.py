# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

{
    'name': "Project Management Custom",
    'summary': """Organize and plan your real estate in project""",
    'description': """ """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',
    'depends': ['project', 'country_city'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/subcontractor_installment_view.xml',
        'views/project_custom_views.xml',
        'views/work_item_view.xml',
        'views/project_estimated_quantities_view.xml',
        'views/project_config_view.xml',
        'views/res_partner_inherit.xml',
        'views/project_main_menus.xml',
        'views/engineering_office_view.xml',
        'views/project_payment_view.xml',
        'views/subcontractor_office_view.xml',
    ],
    'installable': True,
    'application': False,
}