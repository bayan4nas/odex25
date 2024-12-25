# -*- coding: utf-8 -*-
{
    'name': "Takaful Benefits Portal",

    'summary': """
        Benefits UI """,

    'description': """
        Long description of module's purpose
    """,

    'author': "Expert Ltd.",
    'website': "https://www.exp-sa.com",
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website','odex_benefit'],

    # always loaded
    'data': [
        'views/Benefits_data.xml',
        'views/assets.xml',
        'views/food_surplus.xml',
        'views/zakat.xml',
        'views/food_basket.xml',
        'views/urgent_needs.xml',
        'views/profile.xml',
        'views/good_loan.xml',
        'views/clubs.xml',
        'views/families_loan.xml',
        'views/applications_furnatures.xml'
    ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': True,
}