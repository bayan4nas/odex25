# -*- coding: utf-8 -*-


{
    'name': 'Odex25 Web',
    'category': 'Odex25-base',
    'author': 'Expert Co. Ltd.',
    'website': 'http://www.exp-sa.com',
    'version': '1.0',
    'description':
        """
Odoo Enterprise Web Client.
===========================

This module modifies the web addon to provide Odex design and responsiveness.
        """,
    'depends': ['web'],
    #'auto_install': True,
    'data': [
        'views/webclient_templates.xml',
        'views/login_custom.xml',
        # 'views/customize_menu_seurity.xml'
        ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
    'post_init_hook': 'post_init_setup'
}
