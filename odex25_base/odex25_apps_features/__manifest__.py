# -*- coding: utf-8 -*-
{
    'name': 'Odex25-Apps Feature',
    'version': '14.0.0.1',
    'summary': 'Enhance Odoo with Addons Path Management and Module History Tracking',
     'summary': 'Enhance Odoo with Addons Path Management and History Tracking, with Uninstall Restrictions',
    'description': """
        This custom module extends Odoo's functionality by introducing features related to Addons Path management and tracking module installation, upgrades, and uninstallations.

        Key Features:
        - Addons Path Management: Organize and manage Addons Paths with customizable short names and visually distinctive colors.
        - Module History Tracking: Keep a record of module installation, upgrades, and uninstallations, including the author and timestamp.
        - Uninstall Restrictions: Admins can set an uninstallation password to add an extra layer of security, preventing unauthorized module removal.

        Note: This module should be used by experienced Odoo administrators to enhance system management and tracking capabilities. The Uninstall Restrictions feature adds an extra layer of security to prevent unauthorized module removal.
    """,
    'category': 'Odex25-base',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'license': 'AGPL-3',

    'depends': ['base'],

    'data': [
        'security/ir.model.access.csv',
        'views/ir_module_module_view.xml',
        'views/ir_module_addons_path_view.xml'
        ,'views/upgrade_button_views.xml'
        ,'wizard/base_module_uninstall_views.xml'
        ,'views/ir_module_history_view.xml',
        'views/module_multiple_uninstall.xml',
    ],
    'demo': [

    ],
    'qweb': [],

    'installable': True,
    'auto_install': False,
    'application': False,
}
