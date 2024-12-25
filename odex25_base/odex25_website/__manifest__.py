# -*- coding: utf-8 -*-
{
    'name': 'Odex25 Website',
    'category': 'Odex25-base',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': 'Get the enterprise look and feel',
    'description': """
This module overrides community website features and introduces odex25 look and feel.
    """,
    'depends': ['website'],
    'data': [
        'views/odex25_website_templates.xml',
        'views/help.xml',
    ],
    'installable': True,
    'auto_install': True,
}
