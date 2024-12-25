# -*- coding: utf-8 -*-
{
    'name': "Hide Portal Login DB Selection",

    'summary': "Customization for Backend Themes built for Portal Login DB Selection",

    'description': "Hide Portal Login DB Selection",

    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Odex25-base',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['web','odex25_website'],

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