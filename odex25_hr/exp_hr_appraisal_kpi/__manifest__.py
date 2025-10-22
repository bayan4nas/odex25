# -*- coding: utf-8 -*-
###################################################################################

{
    'name': 'Appraisal KPI',
    'version': '14.0',
    'category': 'HR-Odex',
    'summary': 'Manage Appraisal KPI',
    'description': """
        Helps you to manage Appraisal of your company's staff.
        """,
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'depends': [

       'exp_hr_appraisal', 'kpi_scorecard',

    ],
    'data': [
        'security/appraisal_security.xml',
        'security/ir.model.access.csv',
        'views/appraisal_menuitem.xml',
        'views/kpi_item_view.xml',
        'views/kpi_period_view.xml',
        'views/kpi_skills_view.xml',
        #'views/employee_skills_view.xml',
        'views/employee_goals_view.xml',
        'views/distribution_of_weights_view.xml',
        'views/hr_employee_appraisal_view.xml',
        #'views/last_appraisal_employees_view.xml',
        'data/mail_template.xml',
        'data/seq.xml',
        'report/performance_evaluation_report_view.xml',
        'wizard/performance_evaluation_wizard_view.xml',



    ],
    'installable': True,
    'auto_install': False,
}
