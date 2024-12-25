# -*- coding: utf-8 -*-
{
    'name': "odex_new_website",

    'author' : 'Expert Co. Ltd.',
    'website': 'https://www.exp-sa.com',
    'category' : 'website',
    'version' : '14.0',

    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','website'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'template/index.xml',
        'template/footer.xml',
        'template/header.xml',
        'template/courses.xml',
        'template/resources.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
