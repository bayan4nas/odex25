# -*- coding: utf-8 -*-
{
    'name': "odex25 SAIP HR Recruitmen Nafaz",
    'version': "14.0.0",
    'author': 'Expert Co. Ltd. DEV BY ABUZARALKHATEEP',
    'website': 'http://www.exp-sa.com',
    'summary': "Advanced Features for HR SAIP",
    'description': """
            - Fetch data From National Address in hr.employee and job apply api
            - Fetch data From Nafaz in hr.employee and job apply api
            - Fetch employee data From
            - Redesign Job apply form
            - Add new fields in hr.job
            
    """,
    # any module necessary for this one to work correctly
    'depends': ['hr_job_career_path','website_hr_recruitment'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/config_data.xml',
        'views/website_hr_recruitment_templates.xml',
        'views/hr_applicant_inherit.xml',
        'views/hr_employee_inherit.xml',
    ],
    'demo': [
    ],
}
