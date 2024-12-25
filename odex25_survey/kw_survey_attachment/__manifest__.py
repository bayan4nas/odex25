{
    'name': 'File Question',

    'summary': 'Adds new File Question type, uploaded file stored in answers, '
               'survey attachment',

    'author': 'Kitworks Systems',
"category":"Odex25-Survey/Odex25-Survey",
    'website': 'https://kitworks.systems/',

    'license': 'OPL-1',
    'version': '14.0.1.0.5',

    'depends': [
        'survey', 'mail', 'web_widget_url_advanced',
    ],
    'data': [
        'views/survey_template_view.xml',
        'views/survey_user_input_line_view.xml',
        'views/survey_view.xml',
        'views/assets.xml',
    ],
    'installable': True,

    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],

}
