# -*- coding: utf-8 -*-
{
    'name': "Project Variation Order",
    'summary': """Project Variation Order""",
    'description': """
        Add Variation Order in Your Project
        1- add invoices request related to VO
        2- adjust project phases dates based on VO
    """,
    'category': 'Odex25-Project/Odex25-Project',
    'version': '1.0',
    'depends': ['project_base'],
    'data': [
        'data/project_data.xml',
        'data/mail_data.xml',
        'security/project_security.xml',
        'security/ir.model.access.csv',
        'views/project_variation_order_view.xml',
    ],
}
