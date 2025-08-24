# -*- coding: utf-8 -*-
{
    'name': "odex25 HR Budget Saip",
    'version': '14.0.0',
    'category': 'Odex25 Accounting/Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': "Advanced Features for Budget Management",
    'description': """
            - Add budget line in salary rule
            
    """,
    'depends': ['odex25_budget_saip','hr_termination','exp_official_mission'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/employee_other_request.xml',
        'views/hr_salary_rules_views.xml',
        'views/payroll_account_move_views.xml',
        'views/hr_official_mission.xml',
        'views/employee_overtime_request.xml',
        'views/hr_termination_view.xml',
        'data/mail_template.xml',
        'wizard/overtime_request_reject_wizard_views.xml',
        'wizard/return_state_view.xml',


    ],

}
