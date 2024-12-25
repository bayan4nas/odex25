# -*- coding: utf-8 -*-
{
    'name': "Custom Document Layout Fonts",
    'version': '1.0',
    'category': 'Customizations',
    'summary': "Add custom fonts to the Base Document Layout in Odex",
    'description': """
This module adds custom fonts to the base.document.layout model, allowing users to select from new fonts such as Poppins, Roboto, and others for document templates.
    """,
    'author': "AHIDev",
    'website': "http://www.exp-sa.com",
    'depends': ['base', 'web'],
    'data': [
        'views/webclient.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}