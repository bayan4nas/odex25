# -*- coding: utf-8 -*-


from . import models
from odoo import api, SUPERUSER_ID


def post_init_setup(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Check if the "website" module is installed
    if env['ir.module.module'].search([('name', '=', 'website'), ('state', '=', 'installed')]):
        # Update the menu item with the specific group access
        menu = env.ref('website.menu_website_configuration', raise_if_not_found=False)
        if menu:
            group_website_publisher = env.ref('website.group_website_publisher')
            menu.sudo().write({'groups_id': [(6, 0, [group_website_publisher.id])]})