# -*- coding: utf-8 -*-
{
    'name': "Expert Co. Ltd. Theme",

    'summary': "Customization for Backend Themes built for Expert Co. Ltd.",

    'description': "Expert Co. Ltd. Theme",

    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/resources.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}