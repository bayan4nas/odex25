# -*- coding: utf-8 -*-
{
    'name': "Property Management",

    'summary': """Property Management""",

    'description': """
         - Rental Contract.
         - End of Contract.
         - Rental Payment.
         - configuration for the following:
         - Rental Payment Method.
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['real_estate_marketing', 'sale','base'],

    # always loaded
    'data': [
        'security/property_management_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/rental_contract_views.xml',
        'views/property_conf_views.xml',
        'views/rent_payment_view.xml',
        'views/end_rent_views.xml',
        'views/report_views.xml',
        'views/transfer_contract_view.xml',
        'views/client_requirement_view.xml',
        'wizards/confirm_box_property_view.xml',

    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
