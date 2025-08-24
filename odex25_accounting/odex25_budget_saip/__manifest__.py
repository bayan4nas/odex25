# -*- coding: utf-8 -*-
{
    'name': "odex25 Budget Saip",
    'version': '14.0.0',
    'category': 'Odex25 Accounting/Accounting',
    'author': 'SAIP-IT | Mohamed Zain',
    'website': 'https://saip.gov.sa',
    'summary': "Advanced Features for Budget Management",
    'description': """
            - Add budget line features
            - Add budget item in : budget line, account post, purchase request, purchase order, contract, bill, payment
            - add check budget in : purchase request, contract
            - add new computed fields in budget line
            - add budget operation type
            - add budget report
            - add budget operation report
    """,
    'depends': ['odex25_contract_saip', 'odex25_account_saip'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'wizard/add_budget_line_wizard_view.xml',
        'views/account_budget_views.xml',
        'views/item_budget_views.xml',
        'views/budget_confirmation_view.xml',
        'views/purchase_order_views.xml',
        'views/account_move_payment_veiws.xml',
        'views/budget_operations_views.xml',
        'views/budget_menuitem.xml',
        'report/report_actions_view.xml',
        'report/account_budget_pdf_report.xml',
        'report/budget_operation_pdf_report.xml',
        'wizard/account_budget_report_wizard_view.xml',
        'wizard/budget_operation_reject_wizard_views.xml',

    ],

}
