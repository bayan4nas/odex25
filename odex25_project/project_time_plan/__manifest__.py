# -*- coding: utf-8 -*-
{
    'name': "Project Time Plan",
    'summary': """Project Time Plan""",
    'author': "My Company",
    'description': """
        Dividing the Hours or Days of the project phases into the weeks or months of the phase
    """,
    'category': 'Odex25-Project/Odex25-Project',
    'version': '0.1',
    'depends': ['project_base','web_widget_x2many_2d_matrix'],

    'data': [
        'security/ir.model.access.csv',
        'views/project_time_plan_view.xml',
        'views/res_config_setting.xml',
        'views/project_phase_views.xml',
        'views/time_plan_detail.xml',
        'wizard/week_generation_wizard_views.xml',
        'wizard/edit_project_phase_view.xml',
    ],
}
