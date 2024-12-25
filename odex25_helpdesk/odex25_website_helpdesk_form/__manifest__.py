# -*- coding: utf-8 -*-

{
    'name': 'Online Ticket Submission',
    'sequence': 58,
    'summary': 'Qualify helpdesk queries with a website form',
     'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Helpdesk/Odex25-Helpdesk',
    'depends': [
        'website_form',
        'odex25_website_helpdesk',
        'odex25_helpdesk_security',
    ],
    'description': """
Generate tickets in Helpdesk app from a form published on your website. This form can be customized thanks to the *Form Builder* module (available in Odoo Enterprise).
    """,
    'data': [
        'data/odex25_website_helpdesk.xml',
        'views/helpdesk_views.xml',
        'views/helpdesk_templates.xml'
    ],
    'post_init_hook': 'post_install_hook_ensure_team_forms',
}
