# -*- coding: utf-8 -*-
{
    'name': "Project Metrics",
    'summary': """Project Metrics""",
    'category': 'Odex25-Project/Odex25-Project',
    'description': """
       Add Project Metrics that calculated from tasks progress
       and time plan and project counsumed hours
       
    """,
    'version': '0.1',
    'depends': ['project_time_plan'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_metrics_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
    ],
}
