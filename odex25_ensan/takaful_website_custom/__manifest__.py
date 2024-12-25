# -*- coding: utf-8 -*-

{
    'name': 'Takaful Website Custom',
    'version': '1',
    'license': 'GPL-3',
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'summary': 'Takaful Website',
    'description': """
Takaful Website
""",
    'author': 'Expert co.Ltd',
    'website': 'exp-sa.com',
    'depends': ['takaful_core'],
    'data': [
        'data/product_tags_data.xml',
        'data/payment_methods_data.xml',
        'views/product_inherit.xml',
        'views/sales_gifts.xml',
    ],
    'installable': True,
    'application': True,
}

