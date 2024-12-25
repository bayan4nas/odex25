# -*- coding: utf-8 -*-

from odoo import api, fields, models


class BlogPosts(models.Model):
    _inherit = "blog.post"
    
    post_img = fields.Binary(string='Post Image',required=True)

    