# -*- coding: utf-8 -*-
##########################################################
###                 Disclaimer                         ###
##########################################################
### Lately, I started to get very busy after I         ###
### started my new position and I couldn't keep up     ###
### with clients demands & requests for customizations ###
### & upgrades, so I decided to publish this module    ###
### for community free of charge. Building on that,    ###
### I expect respect from whoever gets his/her hands   ###
### on my code, not to copy nor rebrand the module &   ###
### sell it under their names.                         ###
##########################################################

{
    'name': 'Dynamic Workflow  Mobile  Builder',
    'version': '1.0',
    'sequence': '10',
    'category': 'Odex25-Mobile/Odex25-Mobile',
    'author': 'Abuzar Alkhateeb, Expert Co. Ltd.',
    'company': 'Exp-co-ltd',
    'website': 'http://exp-sa.com',
    'summary': 'Dynamic Workflow  Mobile Builder',
    'images': [
        'static/description/banner.png',
    ],
    'description': """
Dynamic Workflow Builder Mobile 
========================
* You can build dynamic workflow Mobile  for any model.
""",
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/odoo_workflow_view.xml',
        'data/flows_data.xml',
    ],
    'depends':['odex_mobile','attendances'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
