# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################
{
    'name': "Real Estate Marketing Sommes and Pricing",
    'summary': """Real Estate Marketing Sommes and Pricing""",
    'description': """
        - define sommes, pricing.
    """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',
    'depends': ['real_estate'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/re_pricing_view.xml',
        'views/re_sommes_view.xml',
        'views/internal_property_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
