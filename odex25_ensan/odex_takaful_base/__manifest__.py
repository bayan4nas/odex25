{
    'name': 'Odex Takaful Base',
    'version': '11.0',
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': 'Base module for Takaful project',
    'depends': ['mail','account'],
    'data': [
        'security/takaful_security.xml',
        'security/ir.model.access.csv',
        'views/takaful_notification_view.xml',
        'views/takaful_config_settings_view.xml',
        # 'views/menu_security_customization.xml'
    ],
    # 'installable': True,
    # 'application': True,
    # 'auto_install': False,
}
