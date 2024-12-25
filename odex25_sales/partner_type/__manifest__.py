# -*- coding: utf-8 -*-

{
    'name': 'Partner Type',
    'version': '1.0',
    'license': 'AGPL-3',
    'category':'Odex25-Sales/Odex25-Sales',
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'summary': "Partner Type ",
    'depends': ['product','account'],
    'data': [
        'security/security_group.xml',
        'views/account_journal_view.xml',
        'views/res_partner_view.xml',
    ],

    'installable': True,
    'application': False,
}