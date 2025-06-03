# -*- coding: utf-8 -*-
{
    'name': 'Purchase Requisition Custom',
    'version': '1.1',
    'summary': 'Adding new Functionality on the Purchase Agreements',
    'sequence': -1,
    'description': """
        Adding new Functionalities in Purchase Agreements
    """,
    'data': [
        'security/category_groups.xml',
        'security/ir.model.access.csv',
        'security/rules.xml',
        'data/purchase_sequence.xml',
        'data/purchase_request_seq.xml',
        'data/cron_data.xml',
        'views/purchase_requisition_custom.xml',
        'views/purchase_request.xml',
        'views/res_setting.xml',
        'views/vendor_type.xml',
        'wizards/cancel_purchase_request.xml',
        'wizards/convert_to_contract.xml',
        'reports/external_layout.xml',
        'reports/committee_meeting_minutes_report.xml',
        'views/budget_confirmation.xml',
    ],
    'depends': ['stock', 'purchase_requisition','hr_base', 'project', 'purchase', 'account_budget_custom','account_fiscal_year'],
    'installable': True,
    'application': True,
}
