from odoo import fields, models, api, _


class benefitClub(models.Model):
    _name = 'benefit.club'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'benefit club'

    name = fields.Char()
    benefit_type = fields.Selection(
        string='Benefit Type',
        selection=[('internal', 'internal'),
                   ('external', 'external'),
                   ('both', 'Both'),
                   ],
        required=False, )
    description = fields.Char(
        string='',
        required=False)

    external_ids = fields.Many2many(
        'external.benefits',
        string='')
    subscription_amount = fields.Float(
        string='',
        required=False)

    is_available = fields.Boolean('is_available' ,default=True)

    # location
    # @api.multi
    # def google_map_link(self, zoom=10):
    #
    #     # params = {
    #     # 'q': '%s, %s %s, %s' % (self.street or '', self.city or '', self.zip or '', self.country_id and self.country_id.name_get()[0][1] or ''),
    #     # 'z': zoom,
    #     # }
    #     params = {
    #         'q': '%s' % ('47.1922423,8.5496122'),
    #         'z': zoom,
    #     }
    #     return urlplus('https://maps.google.com/maps', params)

    benefit_programs = fields.Many2many(
        'benefit.programs',
        string='')
    programs_type = fields.Selection(
        string='',
        selection=[('weekly', 'weekly'),
                   ('monthly', 'Monthly'), ],
        required=False, )

    # program_plane = fields.Text(
    #     string="",
    #     required=False)

    program_plane_ids = fields.One2many(
        comodel_name='program.plane.line',
        inverse_name='club_id',
        string='',
        required=False)

    benefit_ids = fields.Many2many(
        'grant.benefit',
        string='Benefit',
        required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)
    requests_total = fields.Integer(string="Requests Total", compute="get_total")

    def action_submit(self):
        self.state = 'waiting_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    def action_done(self):
        self.state = 'done'

    def get_total(self):
        for request in self:
            if request.id:
                requests = request.env['external.request'].sudo().search(
                    [('club_id', '=', request.id), ('state', '=', 'draft')])
                self.requests_total = len(requests)

    def open_external_request(self):
        context = {}
        context['default_club_id'] = self.id
        return {
            'name': _('External Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.external_request_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.external_request_form').id, 'form')],
            'res_model': 'external.request',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': "[('club_id','=',%s)]" % (self.id),
            'target': 'current',
        }


class ProgramPlane(models.Model):
    _name = 'program.plane.line'
    _description = 'Benefit Programs'

    club_id = fields.Many2one('benefit.club')
    benefit_ids = fields.Many2many('grant.benefit', related='club_id.benefit_ids',
                                   string='Benefit',
                                   required=False)
    date_from = fields.Date(
        string='',
        required=False)
    date_to = fields.Date(
        string='',
        required=False)
    activity_type = fields.Many2one(
        comodel_name='benefit.club.activity',
        string='',
        required=False)
    description = fields.Char()
    attendees = fields.Many2many('grant.benefit', domain="[('id','in',benefit_ids)]", )
    score = fields.Float(
        string='',
        required=False)


class ProgramActivity(models.Model):
    _name = 'benefit.club.activity'
    _description = 'Benefit Programs'

    name = fields.Char()
    description = fields.Char()


class BenefitPrograms(models.Model):
    _name = 'benefit.programs'
    _description = 'Benefit Programs'

    name = fields.Char()
    description = fields.Char()
    behaviors_programs = fields.Many2many(
        'benefit.behaviors.type',
        string='')


class ExternalRequest(models.Model):
    _name = 'external.request'
    _rec_name = 'external_id'
    _description = 'External Request'

    club_id = fields.Many2one(
        comodel_name='benefit.club',
        string='',
        required=False)
    zkat_id = fields.Many2one(
        comodel_name='benefit.zkat',
        string='',
        required=False)

    external_id = fields.Many2one(
        'external.benefits',
        string='External Benefit')
    country_id = fields.Many2one('res.country', related='external_id.country_id', string='Country')
    state_id = fields.Many2one('res.country.state', related='external_id.state_id', string='Country State')
    city_id = fields.Many2one('res.country.city', related='external_id.city_id', string='City')
    street = fields.Char(string='District', related='external_id.street')
    location = fields.Char(string='location', related='external_id.location')
    lat = fields.Char()
    lon = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
    ], string='state', default="draft", tracking=True)

    def action_accept(self):
        self.state = 'approve'
        if self.club_id:
            for id in self.club_id:
                id.write({'external_ids': [(4, self.external_id.id)]})
        if self.zkat_id:
            for id in self.zkat_id:
                id.write({'external_ids': [(4, self.external_id.id)]})

    def action_refused(self):
        self.state = 'refused'
