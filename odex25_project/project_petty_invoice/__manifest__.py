# -*- coding: utf-8 -*-
{
    'name': "Project Petty Invoice",
    'summary': """Project/Account""",
    'category': 'Odex25-Project/Odex25-Project',
    'description': """
    Mark invoice as created from petty project
    """,
    'version': '0.1',
    'depends': ['petty_invoice','project_base'],
    'data': [
        'views/project_invoice_view.xml',
    ],
}
