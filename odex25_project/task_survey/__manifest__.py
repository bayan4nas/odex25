# -*- coding: utf-8 -*-
{
    'name': "Tasks Survey",
    'summary': """ build survey for task""",
    'description': """This addon made for task to build survey from this task""",
    'author': "Expert",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '14.0.1.9',
    'depends': ['base','project_base','survey'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/project_task_survey.xml',
        'views/templates.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
