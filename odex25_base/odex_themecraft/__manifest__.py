# -*- coding: utf-8 -*-
{
    'name': 'Odex ThemeCraft',
    'category': 'Tools',
    'version': '0.4',
    'summary': 'Odex ThemeCraft empowers Odoo users to unleash their creativity and design stunning odoo system that reflect their brand identity and vision. With its intuitive interface and powerful customization features, Odex ThemeCraft revolutionizes the way users approach odoo backend theming in Odoo.',
    'description': 'Odex ThemeCraft is a comprehensive theme customization module for Odoo, designed to empower users with the ability to tailor their Odoo backend themes according to their unique brand identity and preferences. With Odex ThemeCraft, users can effortlessly personalize the look and feel of their odoo system, ensuring it aligns perfectly with their brand image and style.',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'license': '',
    'depends': ['web','odex25_web','web_widget_colorpicker'],
    'data': [
        'views/webclient.xml',
        'views/ir_settings.xml',
    ],
    'pre_init_hook': 'test_pre_init_hook',
    'installable': True,
    'auto_install': False,
    'application': True,
}
