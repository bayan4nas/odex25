# -*- coding: utf-8 -*-
{
    'name': 'Events Website Custom',
    'version': '1.0',
    'website': 'https://www.odoo.com/page/events',
    'category': 'Odex25-Event/Odex25-Event',
    'summary': 'Add Extra Features to Event stander module',
    'description': """
Events Custom.
==============

Key Features
------------
* Edit in Email Schedule Add appility to send emails to Attendees after change in tracks 
* ...
""",
    'depends': ['event_custom'],
    'data': [
        "views/events.xml",
        "views/event_details.xml"
    ],
    'installable': True,
    'auto_install': False,
}
