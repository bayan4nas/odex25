# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from werkzeug import urls
from odoo import models, fields, api


class Slide(models.Model):
    _inherit = 'slide.slide'

    def action_publish(self):
        if not self.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _("Please save the course to publish it.")
                }
            }
        else:
            self.is_published = True

    def action_unpublish(self):
        self.is_published = False

class Channel(models.Model):
    _inherit = 'slide.channel'

    description_short = fields.Html('Short Description', help="The description that is displayed on the course card")
    description = fields.Html('Description', help="The description that is displayed on top of the course page, just below the title")
    YOUTUBE_VIDEO_ID_REGEX_PRO = r'^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*'
    GOOGLE_DRIVE_DOCUMENT_ID_REGEX_PRO = r'(^https:\/\/docs.google.com|^https:\/\/drive.google.com).*\/d\/([^\/]*)'
    intro_video_type = fields.Selection([
        ('youtube_video', 'YouTube Video'),
        ('google_drive_video', 'Google Drive Video')],
        string="Slide Type", compute='_compute_intro_video_type', store=True, readonly=False,
        help="Subtype of the video category, allows more precision on the actual file type / source type.")
    intro_url = fields.Char('External URL', help="URL of the Google Drive file or URL of the YouTube video")
    intro_video_url = fields.Char('Introduction Video Link', related='intro_url', readonly=False,
        help="Link of the video (we support YouTube, Google Drive as sources)")
    intro_video_source_type = fields.Selection([
        ('youtube', 'YouTube'),
        ('google_drive', 'Google Drive')],
        string='Video Source', compute="_compute_intro_video_source_type")
    video_image_1920 = fields.Image(store=True, readonly=False)
    intro_youtube_id = fields.Char('Video YouTube ID', compute='_compute_intro_youtube_id')
    intro_google_drive_id = fields.Char('Google Drive ID of the external URL', compute='_compute_intro_google_drive_id')
    video_embed_code = fields.Html('Embed Code', readonly=True, compute='_compute_video_embed_code', sanitize=False)
    
    @api.depends('intro_video_url', 'intro_google_drive_id', 'intro_video_source_type', 'intro_youtube_id')
    def _compute_video_embed_code(self):
        for course in self:
            video_embed_code = False
            if course.intro_video_url :
                if course.intro_video_source_type == 'youtube':
                    query = urls.url_parse(course.intro_video_url).query
                    query = query + '&theme=light' if query else 'theme=light'
                    video_embed_code = '<iframe src="//www.youtube-nocookie.com/embed/%s?%s" allowFullScreen="true" frameborder="0" style="height:-webkit-fill-available; width:-webkit-fill-available;"></iframe>' % (course.intro_youtube_id, query)
                elif course.intro_video_source_type == 'google_drive':
                    video_embed_code = '<iframe src="//drive.google.com/file/d/%s/preview" allowFullScreen="true" frameborder="0" style="height:-webkit-fill-available; width:-webkit-fill-available;"></iframe>' % (course.intro_google_drive_id)
            course.video_embed_code = video_embed_code

    
    @api.depends('intro_video_type', 'intro_video_source_type')
    def _compute_intro_video_type(self):
        """ For 'local content' or specific slide categories, the slide type is directly derived
        from the slide category.

        For external content, the slide type is determined from the metadata and the mime_type.
        (See #_fetch_google_drive_metadata() for more details)."""
        for course in self:
            if course.intro_video_url and course.intro_video_source_type == 'youtube':
                course.intro_video_type = 'youtube_video'
            elif course.intro_video_url and course.intro_video_source_type == 'google_drive':
                course.intro_video_type = 'google_drive_video'
            else:
                course.intro_video_type = False
    
    @api.depends('intro_video_url')
    def _compute_intro_video_source_type(self):
        for course in self:
            intro_video_source_type = False
            youtube_match = re.match(self.YOUTUBE_VIDEO_ID_REGEX_PRO, course.intro_video_url) if course.intro_video_url else False
            if youtube_match and len(youtube_match.groups()) == 2 and len(youtube_match.group(2)) == 11:
                intro_video_source_type = 'youtube'
            if course.intro_video_url and not intro_video_source_type and re.match(self.GOOGLE_DRIVE_DOCUMENT_ID_REGEX_PRO, course.intro_video_url):
                intro_video_source_type = 'google_drive'

            course.intro_video_source_type = intro_video_source_type

    @api.depends('intro_video_url', 'intro_video_source_type')
    def _compute_intro_youtube_id(self):
        for course in self: 
            if course.intro_video_url and course.intro_video_source_type == 'youtube':
                match = re.match(self.YOUTUBE_VIDEO_ID_REGEX_PRO, course.intro_video_url)
                if match and len(match.groups()) == 2 and len(match.group(2)) == 11:
                    course.intro_youtube_id = match.group(2)
                else:
                    course.intro_youtube_id = False
            else:
                course.intro_youtube_id = False

    @api.depends('intro_video_url')
    def _compute_intro_google_drive_id(self):
        """ Extracts the Google Drive ID from the url based on the slide category. """
        for course in self:
            url = course.intro_video_url
            intro_google_drive_id = False
            if url:
                match = re.match(self.GOOGLE_DRIVE_DOCUMENT_ID_REGEX_PRO, url)
                if match and len(match.groups()) == 2:
                    intro_google_drive_id = match.group(2)

            course.intro_google_drive_id = intro_google_drive_id
