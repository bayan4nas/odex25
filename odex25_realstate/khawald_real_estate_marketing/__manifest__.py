# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

{
    'name': "Real Estate Marketing - Khawald",
    'summary': """Real Estate Marketing""",
    'description': """ """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'category': 'Odex25-Realstate/dex25-Realstate',
    'version': '0.1',
    'depends': ['real_estate_marketing', 'khawald_project_contract','contract'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'wizard/return_payment_view.xml',
        'views/res_partner_view.xml',
        'views/property_reservation_payment_view.xml',
        'views/real_estate_view.xml',
        'views/re_sale_view.xml',
        'views/client_requirement_view.xml',
        'views/property_reservation_view.xml',
        'views/re_unit_view.xml',
        'data/templates.xml',
        'data/ir_seq_data.xml',
        'views/contract_view.xml',

    ],
    'installable': True,
    'application': False,
}
