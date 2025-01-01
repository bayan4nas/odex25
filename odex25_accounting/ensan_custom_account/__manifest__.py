{
    'name': 'Ensan Custom Account Enhancements',
    'summary': 'Adds enhancements to the accounting module including modifications to account forms and views.',
    'description': """
        This module introduces several enhancements to the accounting functionality in Odoo. 
        It modifies account forms and views to improve user experience and add additional features.
        Specifically, it adjusts the selection of accounts available in various forms and ensures 
        compatibility with related modules.
    """,
    'version': '1.0',
    'category': 'Odex25-Accounting/Odex25-Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'depends': ['base',
                'account',
                'odex25_account_budget',
                'account_chart_of_accounts',
                ],
    'data': [
        'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
