# -*- coding: utf-8 -*-
{
    'name': 'Logout Idle User',
    'version': '14.0.1.0.0',
    'summary': 'Auto logout idle user with fixed time',
    'description': """set limitation on the user session in setting, if the user
     is in idle mode the user will logout from session 
     automatically""",
    'category': 'Extra Tools',
    'author': 'Saip-IT',
    'license': 'AGPL-3',
    'depends': ['base_setup'],
    'data': [
        'views/res_users_views.xml',
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/systray.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}
