# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################
{
    'name': "Real Estate Marketing",
    'summary': """Real Estate Marketing""",
    'description': """
        - define Client Requirement.
        - Create Sale property/Unit to client.
    """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',
    'depends': ['real_estate', 'account'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/res_config_setting_view.xml',
        'views/client_requirement_view.xml',
        'views/re_sale_view.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
}
