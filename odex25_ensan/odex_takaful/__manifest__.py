{
    'name': 'Odex Takaful System',
    'version': '11.0',
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': 'This module for Takaful project',
    'depends': [
        'base',
        'takaful_core',
        'odex_takaful_base', 
        'odex_benefit',
        'account',
        # 'analytic_account',
    ],
    'data': [
        'security/security_data.xml',
        'security/ir.model.access.csv',

        'data/sequence_data.xml',
        'data/scheduled_actions.xml',
        'data/takaful_notification_mail_template.xml',

        'views/takaful_sponsor_view.xml',
        'views/takaful_sponorship_view.xml',
        'views/takaful_res_partner_view.xml',

        'views/takaful_contribution_view.xml',
        'views/sponsorship_payment_view.xml',
        'views/sponsorship_cancellation_view.xml',

        'views/takaful_push_notification_view.xml',
        'views/takaful_grant_benefit_view.xml',
        'views/takaful_month_payment_view.xml',
        'wizards/benefit_month_payment_wiz_view.xml',
        'views/takaful_conf.xml',

        'views/reports_paperformats.xml',
        'views/reports_templates.xml',
        'views/reports_actions.xml',
        'reports/month_payment_template.xml',
        'wizards/takaful_reports_wizards.xml',
        'views/takaful_menus_actions.xml',
        'data/message_template_data.xml',
    ],
    # 'installable': True,
    # 'application': True,
    # 'auto_install': False,
}
