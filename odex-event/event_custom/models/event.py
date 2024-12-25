# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

class Track(models.Model):
    _inherit = "event.track"


    # @api.multi
    def write(self, vals):
        if 'date' in vals:
            onchange_schedulers = self.event_id.event_mail_ids.filtered(lambda s: s.interval_type == 'after_change_tracks')
            onchange_schedulers.with_context(track_change={'id':self.id,'change_date_from':self.date,'change_date_to':vals['date']}).execute()
        res = super(Track, self).write(vals)
        return res

class EventEvent(models.Model):
    _inherit = 'event.event'

    directory_id = fields.Many2one('muk_dms.directory', 'Main directory')
    benefit_club_id = fields.Many2one('benefit.club', 'Benefit Club',domain =[('state', '=', 'approve')])
    event_dms_file_ids = fields.One2many('dms.file', 'event_id', string='Files', copy=False)
    count_files = fields.Integer(
        compute='_compute_count_files',
        store=True,
        string="Files")
    event_mail_ids = fields.One2many('event.mail', 'event_id', string='Mails', copy=False)
    count_mails = fields.Integer(
        compute='_compute_count_mail',
        store=True,
        string="Mails")
    image = fields.Binary("Event Image", attachment=True)
    project_id = fields.Many2one('project.project',string='Project',index=True,tracking=True)

    # @api.multi
    def write(self, vals):
        res = super(EventEvent, self).write(vals)
        for benifit in self.benefit_club_id.benefit_ids:
            values = {
                'email': benifit.email,
                'event_id': self.id,
                'name': benifit.name,
                'phone': benifit.phone}
            registration_exist = self.env['event.registration'].search(
                [('email', '=', benifit.email), ('event_id', '=', self.id)], limit=1)
            if registration_exist:
                continue;
            else:
                self.env['event.registration'].create(values)
        return res

    # @api.onchange('benefit_club_id')
    # def onchange_benefit_club_id(self):
    #     for record in self:
    #         for benifit in record.benefit_club_id.benefit_ids:
    #             values = {
    #                     'email': benifit.email,
    #                     'event_id': self._origin.id,
    #                     'name': benifit.name,
    #                     'phone': benifit.phone }
    #             record.env['event.registration'].create(values)
    #             # record.write({'registration_ids':values})

    @api.depends('event_dms_file_ids')
    def _compute_count_files(self):
        for record in self:
            record.count_files = len(record.event_dms_file_ids)

    @api.depends('event_mail_ids')
    def _compute_count_mail(self):
        for record in self:
            record.count_mails = len(record.event_mail_ids)

    @api.model
    def create(self, vals):
        res = super(EventEvent, self).create(vals)
        if not res.directory_id:
            directory = self.env['muk_dms.directory'].sudo().create({
                'name': res.name,
                'is_root_directory': True,
                #TODO review how to get settings
                'settings': self.env['muk_dms.settings'].search([],limit=1).id,
            })
            res.directory_id = directory.id
        return res

    # @api.multi
    def action_open_files(self):
        """ 
        """
        ctx = dict(
            default_event_id=self.id,
            default_directory=self.directory_id.id,
        )
        return {
            'name': _('Event Files'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'dms.file',
            'target': 'current',
            'context': ctx,
            'domain':[("event_id", "=",  self.id)]
        }

    # @api.multi
    def action_open_mail(self):
        """
        """
        ctx = dict(
            default_event_id=self.id,
            default_directory=self.directory_id.id,
        )
        return {
            'name': _('Event Mails'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.mail',
            'target': 'current',
            'context': ctx,
            'domain': [("event_id", "=", self.id)]
        }


class Sponsor(models.Model):
    _inherit = "event.sponsor"

    date = fields.Datetime(string='Event date', related="event_id.date_begin",store=True)
    event_type_id = fields.Many2one('event.type', string='Category',related="event_id.event_type_id",store=True)

class SponsorType(models.Model):
    _inherit = "event.sponsor.type"

    sponsor_cost = fields.Float("Cost")

class TrackLocation(models.Model):
    _inherit = "event.track.location"

    location_url = fields.Char("Location URL")


