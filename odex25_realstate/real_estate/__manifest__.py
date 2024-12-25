# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

{
    'name': "Real Estate",
    'summary': """Base Real Estate""",
    'description': """
        - define property.
        - define unit and link it with it's property.
        - configuration for the following:
            - cites.
            - district.
            - property faces.
            - property Type.
            - unit types. """,

    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',
    'depends': ['country_city','partner_custom'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/real_estate_menu.xml',
        'views/re_unit_view.xml',
        'views/internal_property_views.xml',
        'views/real_estate_conf_views.xml',
        # 'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,

}
