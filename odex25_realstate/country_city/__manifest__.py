# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

{
    'name': "City and District",
    'summary': """Base City and District""",
    'description': "",
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/dex25-Realstate',
    'version': '0.1',
    'depends': ['base', 'mail',],
    'data': [
        'security/ir.model.access.csv',
        'views/city_district_views.xml',
    ],
    'installable': True,
    'application': True,
}
