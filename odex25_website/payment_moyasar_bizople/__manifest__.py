# -*- coding: utf-8 -*-
# Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details
{
    'name': 'Moyasar Payment Gateway',
    'version': '14.0.0.1',
    'category': 'Odex25-Website/Odex25-Website',
    'sequence': 1,
    'summary': 'Odoo Moyasar Payment Gateway',
    'description': 'Odoo Moyasar Payment Gateway',
    'author': 'Bizople Solutions Pvt. Ltd.',
    'website': 'https://www.bizople.com/',
    'depends': ['base','website_sale','sale'],
    'data': [
        'data/moyasar_data.xml',
        'views/assets.xml',
        'views/payment_acquirer.xml',
        'views/moyasar_form.xml',
        'views/payment_transaction_view.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'price' : 100,
    'currency': 'EUR',
    'external_dependencies': {
        "python" : ["moyasar"],
    },
}
