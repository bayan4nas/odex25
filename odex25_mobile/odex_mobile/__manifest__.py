# -*- coding: utf-8 -*-

{
    'name': 'Odex Moblie Application API',
    'version': '1.0',
    'license': 'AGPL-3',
    'category': 'Odex25-Mobile/Odex25-Mobile',
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'summary': "All Mopile Api and Configurations",
    'depends': [
        'attendances',
        'employee_requests',
        'website',
        # 'project_team',
        'mass_mailing',
        'hr_holidays_public',
        'exp_payroll_custom',
        'hr_timesheet_sheet',
    ],
    'external_dependencies': {
        'python': ['jwt', 'firebase_admin'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/attendance_zone_config_view.xml',
        'views/hr_employee_view.xml',
        'views/firebase_notifications.xml',
        'views/firebase_registration.xml',
        # 'views/resource_calendar.xml',
        'wizard/firebase_registration_wizard.xml',
        'templates/terms.xml',
        'data/zone_crone.xml',
        'data/fcm_cron.xml',
        'data/token_cron.xml',
        'data/employee_notification_cron.xml',
    ],
    'css': [
        'static/src/css/jwt.css',
    ],
    'installable': True,
    'application': False,
}
