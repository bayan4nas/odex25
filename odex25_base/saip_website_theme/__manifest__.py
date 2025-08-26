# -*- coding: utf-8 -*-
{
    'name': "Saudi Authority Website Theme",
    'summary': "Customization for website theme built for Saudi Authority",
    'description': "Saudi Authority Website Theme",
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'category': 'Tools',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['web','website','odex25_hr_recruitment_nafaz','hr_recruitment'],
    # always loaded
    'data': [
        'views/resources.xml',
        'views/custom_jobs.xml',
        'views/footer.xml',
    ],
}