{
    'name': "Odex25- Debrand",

    'summary': """
        Odoo Module for backend and frontend debranding.""",

    'description': """
        To debrand front-end and back-end pages by removing
         odoo promotions, links, labels and other related
         stuffs.
    """,

    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    "category": "Odex25-base",
    'depends': [
        'base_setup',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/mail_template_remove_odoo_views.xml',
        'views/website_footer_brand_promotion.xml',
        'views/ir_ui_menu.xml',
        'views/res_config_settings_views.xml',
        'views/login_image.xml',
        'templates/left_login_template.xml',
        'templates/right_login_template.xml',
        'templates/middle_login_template.xml',
        'templates/assets.xml',
        'views/portal_template.xml',
        'views/webclient_templates.xml'
    ],
    'qweb': ['static/src/xml/base.xml'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
