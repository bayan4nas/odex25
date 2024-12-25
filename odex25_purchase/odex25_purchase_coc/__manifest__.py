# -*- coding: utf-8 -*-
{
    'name': "Purchase CoC",

    'summary': """
        This Module is Designed and Developed to Add CoC process To purchase""",

    'description': """
        
    """,

    'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Purchase/Odex25-Purchase',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': ['purchase_requisition_custom'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'sequence/seq.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
