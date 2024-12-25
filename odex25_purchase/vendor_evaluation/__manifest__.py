# -*- coding: utf-8 -*-
{
    'name': "Vendor Evaluation",

    'summary': """
       Evaluating vendors in purchase context""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Purchase/Odex25-Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase','purchase_requisition_custom'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/evaluatioin_criteria_veiw.xml',
        'views/purchase_orde_view.xml',
        'views/vendor_evaluatoin_view.xml',
        'views/res_models_views.xml',
        'views/stock.xml',
        'views/account_invoice_view.xml',
        'views/reports.xml',
        'views/templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
}