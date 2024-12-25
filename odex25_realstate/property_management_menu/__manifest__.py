# -*- coding: utf-8 -*-
{
    'name': "Property Management - Menu",

    'summary': """""",

    'description': """
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'property_management'],

    # always loaded
    'data': [
        'views/property_management_menu_view.xml',

    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
}
