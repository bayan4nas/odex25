# -*- coding: utf-8 -*-
{
    'name': 'Takaful System REST API',
    'version': '11.0.1.14.8',
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': """Enhanced RESTful API access to System resources.""",
    'external_dependencies': {
        'python': ['simplejson'],
    },
    'depends': [
        'base',
        'web',
        'odex_takaful', 
        'odex_benefit', 
    ],
    'data': [       
        'security/ir.model.access.csv',
        'data/ir_configparameter_data.xml',
        'data/ir_cron_data.xml',
        'templates/paying_operation.xml',
        'templates/resources.xml',
    ],
    # 'installable': True,
    # 'application': True,
    # 'auto_install': False,
}
