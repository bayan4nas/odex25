# -*- coding: utf-8 -*-
{
    'name' : 'Partnerhip Website Logo',
    'summary' : 'Odoo module for partnership logo and details to display on website',
    'description' : """
        Partnership Website ======================================= Using To display partnership's logos on Website
    """,
    'author' : 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'category' : 'Odex25-Website/Odex25-Website',
    'version' : '11.0.1.0.0',
    'sequence' : 1,
    'depends' : ['base','website','web'],
    'data': [
        'views/partnership_website.xml',
        'security/ir.model.access.csv',
    ],
    'qweb' : [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'external_dependancies': [],
}
