# -*- coding: utf-8 -*-

{
    'name': 'Helpdesk Stock',
    'summary': 'Project, Tasks, Stock',
    'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Helpdesk/Odex25-Helpdesk',
    'depends': ['odex25_helpdesk_sale', 'stock'],
    'auto_install': False,
    'description': """
Manage Product returns from helpdesk tickets
    """,
    'data': [
        'wizard/stock_picking_return_views.xml',
        'views/odex25_helpdesk_views.xml',
    ],
    'demo': ['data/odex25_helpdesk_stock_demo.xml'],
}
