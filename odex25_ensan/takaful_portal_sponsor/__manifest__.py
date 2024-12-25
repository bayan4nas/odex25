# -*- coding: utf-8 -*-
{
    'name': "Takaful Sponsor Portal",

    'summary': """
        Web portal fo takafaul sponsor """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Expert Ltd.",
    'website': "https://www.exp-sa.com",
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        'views/kafel_header.xml',
        'views/kafel.xml',
        'views/makfoul_details.xml',
        'views/need_kafala_details.xml',
        'views/financial_record.xml',
        'views/notifications.xml',
        'views/notifications_settings.xml',
        'views/certificates_settings.xml',
        'views/profile.xml',
        'views/assets.xml',
        ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': True,
}