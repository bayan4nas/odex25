# -*- coding: utf-8 -*-
{
    "name": """Custom Gantt Native view for Projects""",
    "category": "Odex25-Project/Odex25-Project",
    "version": "14.1",
    "description": """
        Gantt View for Project and Project Task
    """,
    "author": "Expert",
    "website": "https://exp-sa.com/web",



    "depends": [
        "project_base",
        "project_native",
        "project_native_report_advance",
    ],

    "data": [
        'security/security.xml',
        'views/project_task_view.xml',
        'views/project_project_view.xml',
    ],

    "installable": True,
    
}
