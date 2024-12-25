{
    'name': 'Odex Web App API',
    'version': '1.0',
    'license': 'AGPL-3',
    'category': 'Odex25-Mobile/Odex25-Mobile',
    'author': 'Expert Co. Ltd.',
    'website': 'http://exp-sa.com',
    'summary': "All Mopile Web App Api and Configurations",
    'depends': ['hr'],
    'external_dependencies': {
        'python': ['jwt', ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/attendance_zone_config_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
}
