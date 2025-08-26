# __manifest__.py

{
    'name': 'Pandora Login Via 2FA (Via Employee Mobile & Email)',
    'version': '14.0.1.0.0',
    'summary': 'Allow users to login via 2FA (Via Employee Mobile & Email) - Configure Any SMS API & Mail Server',
    'description': """
        Pandora Login Via 2FA
        ================================
        This module allows users to log in via two-factor authentication using their registered mobile phone number or email address. 

        Features:
        - User authentication via OTP sent to mobile or email.
        - Option to remember devices for future logins without OTP.
        - Management of trusted devices.
        - Configuration of SMS API and email server for OTP delivery.
    """,
    'category': 'Extra Tools',
    'author': 'Pandoratech, Shawal Ahmad Mohmand',
    'company': 'Pandorat3ch',
    'maintainer': 'Shawal Ahmad Mohmand',
    'website': 'https://www.pandoratech.ae',
    'depends': ['base', 'web', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/login_templates.xml',
        'views/apis_views.xml',
        'views/views.xml',
        'data/data.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 99,
    'currency': 'USD',
    'license': 'OPL-1',
    'support': 'support@pandoratech.ae',
}
