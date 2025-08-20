
{
    'name': 'SAIP Contracts AND COC Contract Management',
    'version': '14.0..1.0',
    'category': 'Contract Management',
    'license': 'AGPL-3',
    'author': "Expert - dev By ABUZAR",
    'website': '',
    'depends': ['contract'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/seq.xml',
        'views/contract_view_inherit.xml',
        'views/contract_installment_line_view_inherit.xml',
        'views/purchase_view_inherit.xml',
        'views/account_move_view_inherit.xml',
        'wizard/installment_reject_wizard_views.xml',
        'wizard/return_state_view.xml',
        'wizard/installment_return_state_view.xml',
    ],
}
