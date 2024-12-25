# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'EXP Helpdesk Assignation methods',
    'summary': 'Ticket Assignation methods for team members considering ticket types',
    'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Helpdesk/Odex25-Helpdesk',
    'depends': ['odex25_helpdesk_security'],
    'description': """
        Ticket Assignation methods for team members considering ticket types
    """,
    'auto_install': True,
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_views.xml',
    ],
    'license': '',
}
