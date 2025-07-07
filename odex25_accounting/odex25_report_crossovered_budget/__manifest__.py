{
    'name': 'Crossovered Budget Report',
    'version': '14.0.1.0.0',
    'summary': 'Custom report for crossovered budget lines',
    'description': """
        This module provides a custom financial report for budget lines
        with extended filters and analysis.
    """,
    'category': 'Accounting/Budget',
    'author': 'Your Name or Company',
    'website': 'https://yourcompany.com',
    'depends': ['account_configuration','account'],
    'data': [
        'wizard/show_budget.xml',
        'security/ir.model.access.csv',

    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
