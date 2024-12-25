# -*- coding: utf-8 -*-
{
    'name': "Takaful Website",

    'summary': """
        Takaful main website template """,

    'description': """
        Takaful main website template
    """,
    'author': "Expert Ltd.",
    'website': "https://www.exp-sa.com",
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['web','website','website_blog'],
    'depends': ['web','website'],

    # always loaded
    'data': [
        'views/assets.xml',
        'views/header.xml',
        'views/footer.xml',
        'views/home.xml',
        # 'views/login.xml',
        'views/registration.xml',
        'views/login_custom.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}