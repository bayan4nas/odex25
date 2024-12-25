{
    'name': 'Odoo Log Viewer',
    'version': '17.0.0.1.0',
    'category': 'Tools',
    'summary': 'View Odoo log in real-time as a web page',
    'sequence': 10,
    'author': 'Abdelrahman Eltayar',
    'depends': ['base', 'web'],
    'data': [
        'views/log_viewer_template.xml',
        'views/assets.xml',
        'data/ir_config_parameter.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_log_viewer/static/src/css/log_viewer_style.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}