# -*- coding: utf-8 -*-

{
    'name': 'Web Hijri',
    'category' : 'Odex25-base',
    'version': '1.0',
    'description': """Enable Web Hijri Datepicker in Odoo""",
    'depends': ['web'],
    'data': ['views/web_hijri_template.xml'],
    'qweb': ["static/src/xml/web_hijri_date.xml"],
    'installable': True,
    'auto_install': False,
    'bootstrap': True,
    'application': True,
}
