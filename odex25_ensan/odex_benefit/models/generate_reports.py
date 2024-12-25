import base64
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError


class ReportLog(models.Model):
    _name = 'generate.reports.log'
    _description = 'Reports log'

    name = fields.Char()
    datetime = fields.Datetime()
    user_id = fields.Many2one('res.users')
    attach = fields.Binary(string="", )


class GenerateReports(models.TransientModel):
    _name = 'generate.reports'
    _description = 'Generate Reports For Benefits'

    name = fields.Char()
    current_user = fields.Many2one('res.users', 'Current User', default=lambda self: self.env.user)
    service_to = fields.Selection(
        selection=[('benefit', 'Benefit'),  # 1
                   ('family', 'Family'),  # 2
                   ('house', 'House')])  # 3
    service_category = fields.Selection(
        string='', selection=[('financial', 'financial'),
                              ('In-kind', 'In-kind'),
                              ('seasonal', 'seasonal'), ])
    house_service_category = fields.Selection(
        string='', selection=[('financial', 'financial'),
                              ('In-kind', 'In-kind'),
                              ('fittings', 'fittings'),
                              ('car_need', 'car need'),
                              ])
    benefit_service_category = fields.Selection(
        string='', selection=[('financial', 'financial'),
                              ('In-kind', 'In-kind'),
                              ('teaching', 'teaching'),
                              ('qualification', 'qualification'),
                              ('training', 'training'),
                              ('omra', 'omra'),
                              ])
    seasonal_service_type = fields.Selection(
        string='', selection=[
            ('zkat', 'zkat alfeter'),
            ('sacrifice', 'sacrifice')
        ])
    service_type = fields.Selection(
        string='', selection=[
            ('urgent', 'urgent'),
            ('non-urgent', 'non-urgent'),
        ])
    # position = fields.Selection(string="Position",
    #                             selection=service_to_benefit + service_to_benefit,
    #                             compute='calculation_list', store=True)
    # service_to_benefit = fields.Selection(string='Company Position', selection=service_to_benefit)
    housing_financial_type = fields.Selection(
        string='', selection=[
            ('rent', 'rent amount'),
            ('maintenance', 'maintenance expenses'),
            ('expenses', 'All expenses'),
        ])
    qualification_type = fields.Selection(
        string='', selection=[
            ('fat', 'fat'),
            ('behavior', 'behavior'),
        ])
    teaching_type = fields.Selection(
        string='', selection=[
            ('literacy', 'Literacy'),
            ('memorization', 'memorization'),
            ('specialty', 'specialty'),
        ])
    report_file = fields.Binary(string="", )

    education_status = fields.Selection(string='Education Status',
                                        selection=[('educated', 'educated'), ('illiterate', 'illiterate')])
    case_study = fields.Selection(string='Education Status', selection=[('continuous', 'continuous'),
                                                                        ('intermittent', 'intermittent')])
    category_id = fields.Many2many('benefit.category')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    date_from = fields.Datetime()
    date_to = fields.Datetime()
    club_programs = fields.Many2one('benefit.programs', string='')
    age_from = fields.Integer()
    age_to = fields.Integer()
    max_rent = fields.Integer()
    family_id = fields.Many2many('benefit.family','benefit_family_group_rel','generate_id','benefit_id')
    benefit_id = fields.Many2many('grant.benefit')
    housing_id = fields.Many2many('benefit.housing')
    housing_room_ids = fields.Many2many('housing.rooms.members')
    housing_rent_ids = fields.Many2many('housing.need')
    specialization_id = fields.Many2one('specialization.specialization')
    product_id = fields.Many2one('product.product')
    appliances_furniture_need = fields.Many2many('appliances.furniture.need')
    # appliances_furniture_need = fields.Many2many('benefit.housing.rooms')
    behavior_id = fields.Many2one('benefit.behaviors.type')
    training_type_id = fields.Many2one('training.type')
    percentage = fields.Float()
    benefit_ids = fields.Many2many('grant.benefit', 'benefits', 'id_number', 'birth_date')
    benefit_f_needs_percent = fields.Many2many('grant.benefit', 'financial', 'id_number', 'birth_date')
    benefit_qualification_ids = fields.Many2many('grant.benefit', 'qualification', 'id_number', 'birth_date')
    benefit_teaching_ids = fields.Many2many('grant.benefit', 'teaching', 'id_number', 'specialization_ids')
    benefit_training_ids = fields.Many2many('grant.benefit', 'training', 'id_number', 'specialization_ids')
    benefit_omra_ids = fields.Many2many('grant.benefit', 'benefits_omra', 'age', 'amra_date')
    black_list = fields.Many2many('grant.benefit', 'black_list', 'id_number', 'is_zakat_fitr')
    housing_need_car_ids = fields.Many2many('benefit.housing', 'cars', 'name', 'benefit_ids')
    benefits_need_ids = fields.Many2many('benefits.needs')
    family_need_ids = fields.Many2many('benefit.family')
    description = fields.Char()
    fat = fields.Float(default=30.0)

    @api.onchange('service_to', 'service_type', 'benefit_service_category', 'house_service_category',
                  'service_category', 'behavior_id', 'seasonal_service_type',
                  'product_id', 'qualification_type',
                  'teaching_type', 'housing_financial_type', 'behavior_id')
    def calculation(self):
        domain = []
        domain += [('age', '>=', self.age_from), ('age', '<=', self.age_to if self.age_to != 0 else 3000)]
        if self.service_to == 'benefit':  # 1
            # 1
            if self.benefit_service_category == 'financial':
                ids = []
                benefits_f_need = self.env['grant.benefit'].sudo().search([])
                for i in benefits_f_need:
                    if i.benefit_needs_percent >= self.percentage:
                        ids.append(i.id)
                self.benefit_f_needs_percent = ids
                # 2
            if self.benefit_service_category == 'In-kind' and self.product_id:
                if self.service_type == 'urgent':
                    benefits_need = self.env['benefits.needs'].sudo().search(
                        [('state', 'in', ['approve', 'published']), ('need_status', '=', 'urgent'),
                         ('need_type_ids', 'in', self.product_id.id)])
                if self.service_type == 'non-urgent':
                    benefits_need = self.env['benefits.needs'].sudo().search(
                        [('state', 'in', ['approve', 'published']), ('need_status', '=', 'not_urgent'),
                         ('need_type_ids', 'in', self.product_id.id)])
                if self.service_type:
                    self.benefits_need_ids = [(6, 0, benefits_need.ids)]
            # 3
            if self.benefit_service_category == 'omra':  # B
                benefits = self.env['grant.benefit'].sudo().search(domain)
                self.benefit_omra_ids = [(6, 0, benefits.ids)]
            # 4
            if self.benefit_service_category == 'qualification':  # 2
                if self.qualification_type == 'behavior':
                    benefits_list = []
                    benefits = self.env['grant.benefit'].sudo().search(domain)
                    for i in benefits:
                        for x in i.benefit_behavior_ids:
                            if self.behavior_id.id == x.behavior_id.id:
                                benefits_list.append(i.id)
                    self.benefit_qualification_ids = [(6, 0, benefits_list)]
                if self.qualification_type == 'fat':  # 5
                    domain += [('p_weight', '>', self.fat)]
                    benefits = self.env['grant.benefit'].sudo().search(domain)
                    self.benefit_qualification_ids = [(6, 0, benefits.ids)]
            # 5
            if self.benefit_service_category == 'teaching':  # 5
                if self.teaching_type == 'literacy':
                    domain += [('education_status', '=', 'illiterate')]
                    benefits = self.env['grant.benefit'].sudo().search(domain)
                    # self.benefit_teaching_ids = [(6, 0, benefits.ids)]
                if self.teaching_type == 'memorization':
                    domain += [('is_quran_memorize', '=', True)]
                    benefits = self.env['grant.benefit'].sudo().search(domain)
                    # self.benefit_teaching_ids = [(6, 0, benefits.ids)]
                if self.teaching_type == 'specialty':
                    domain += [('specialization_ids', '=', self.specialization_id.id)]
                    benefits = self.env['grant.benefit'].sudo().search(domain)
                if self.teaching_type:
                    self.benefit_teaching_ids = [(6, 0, benefits.ids)]
            # 6
            if self.benefit_service_category == 'teaching':  # 5
                if self.training_type_id:
                    self.benefit_teaching_ids = [(6, 0, benefits.ids)]
        if self.service_to == 'family':  # 2
            if self.service_category == 'financial':
                ids = []
                benefit_family = self.env['benefit.family'].sudo().search([])
                for i in benefit_family:
                    if i.benefit_needs_percent >= self.percentage:
                        ids.append(i.id)
                self.family_need_ids = ids
                # 2
            if self.service_category == 'seasonal' and self.seasonal_service_type == 'zkat':
                benefits = self.env['grant.benefit'].sudo().search([])
                black_list = self.env['grant.benefit'].sudo().search([('is_zakat_fitr', '=', False)])
                self.black_list = [(6, 0, black_list.ids)]
                benefits_list = []
                for i in benefits:
                    benefits_list.append(i.id)
                for i in black_list:
                    if i.id in benefits_list:
                        if i.id in self.black_list.ids:
                            benefits_list.remove(i.id)
                self.benefit_ids = [(6, 0, benefits_list)]
        if self.service_to == 'house':  # 3
            if self.house_service_category == 'In-kind' and self.product_id:
                for rec in self:
                    rooms = rec.env['benefit.housing.rooms'].sudo().search(
                        [('items.item.name', '=', rec.product_id.name)])
                    room_list = []
                    need_list = []
                    for room in rooms:
                        needs = {}
                        needs["ap_id"] = self._origin.id
                        needs["housing_id"] = room.housing_id.id
                        needs["room_id"] = room.id
                        for test in room.items:
                            if test.item.name == rec.product_id.name:
                                if test.percentage >= self.percentage:
                                    needs["percentage"] = test.percentage
                                    needs["status"] = test.status.id
                                    needs["name"] = test.item.name
                                    room_list.append(room.housing_id.id)
                                    need_list.append(needs)
                    if rooms:
                        benefit = []
                        for room in rooms:
                            benefits = rec.env['grant.benefit'].sudo().search(
                                [('housing_id', '=', room.housing_id.id), ('benefit_type', '=', 'benefit')])
                            for i in benefits:
                                benefit.append(i.id)
                        for r in rec:
                            r.benefit_ids = [(6, 0, benefit)]
                    for ap in self.appliances_furniture_need:
                        for i in range(len(need_list)):
                            if need_list[i]['housing_id'] == ap.housing_id:
                                del need_list[i]
                                break
                    if not self.appliances_furniture_need:
                        for need_item in need_list:
                            self.appliances_furniture_need = [(0, 0, need_item)]
            if self.house_service_category == 'financial' and self.housing_financial_type == 'rent':  # 3
                for rec in self:
                    self.housing_rent_ids = False
                    housing = rec.env['benefit.housing'].sudo().search([('rent_amount', '>=', rec.max_rent)])
                    need_list = []
                    for i in housing:
                        needs = {}
                        needs["ap_id"] = self._origin.id
                        needs["housing_id"] = i.id
                        # needs["benefit_id"] = room.housing_id.id
                        needs["amount"] = i.rent_amount
                        need_list.append(needs)
                        self.housing_rent_ids = [(0, 0, needs)]
            if self.house_service_category == 'fittings':
                for rec in self:
                    rooms = rec.env['housing.rooms.members'].sudo().search(
                        [('is_accept', '!=', True)])
                    self.housing_room_ids = rooms.ids
            if self.house_service_category == 'car_need':
                benefits = self.env['grant.benefit'].sudo().search([])
                ids = []
                for rec in benefits:
                    if rec.car_count == 0:
                        ids.append(rec.id)
                housing = rec.env['benefit.housing'].sudo().search([('benefit_ids', 'in', ids)])
                self.housing_need_car_ids = housing.ids

    @api.onchange('black_list')
    def calculation_2(self):
        if self.service_to == 'family' and self.service_category == 'seasonal' and self.service_type == 'zkat':
            black_list = self.env['grant.benefit'].sudo().search([('is_zakat_fitr', '=', False)])
            benefits_list = []
            for i in black_list:
                if i.id not in self.black_list.ids:
                    benefits_list.append(i.id)
            for x in benefits_list:
                self.benefit_ids = [(4, x)]

    @api.onchange('benefit_ids')
    def calculation_3(self):
        if self.service_to == 'family' and self.service_category == 'seasonal' and self.service_type == 'zkat':
            benefit = self.env['grant.benefit'].sudo().search([])
            black_list = []
            for i in benefit:
                if i.id not in self.benefit_ids.ids:
                    black_list.append(i.id)
            for x in black_list:
                self.black_list = [(4, x)]

    def get_result(self):
        # if self.service_to == 'family' and self.service_category == 'In-kind' and self.service_type == 'zkat':
        benefits_family = {}
        list = []
        for i in self.benefit_ids:
            dic = {}
            dic["family_id"] = i.family_id.id
            count = 0
            for x in self.benefit_ids:
                if x.family_id.id == dic["family_id"]:
                    count += 1
            dic["benefits_total"] = count
            if dic not in list:
                list.append(dic)
        benefit_zkat = self.env['benefit.zkat'].sudo().create({'name': self.name, })
        for i in list:
            benefit_zkat.sudo().write({'zkat_ids': [(0, 0, i)]})

    def create_club(self):
        programs = self.env['benefit.programs'].sudo().search([('behaviors_programs', 'in', self.behavior_id.id)])
        benefit_club = self.env['benefit.club'].sudo().create({'name': self.name, 'benefit_type': 'internal', })
        benefit_club.benefit_programs = programs
        benefit_club.benefit_ids = self.benefit_qualification_ids

    def get_need(self):
        if self.service_to == 'benefit' and self.benefit_service_category == 'financial':
            ids = self.benefit_f_needs_percent.ids
            needs_value = 0.0
            for i in self.benefit_f_needs_percent:
                needs_value += i.benefit_needs_value
            benefit_need_type = ''
            if ids and len(ids) > 1:
                benefit_need_type = 'general'
            elif ids and len(ids) == 1:
                benefit_need_type = 'special'
            benefit_needs = self.env['benefits.needs'].sudo().create({
                'name': self.name,
                'benefit_need_type': benefit_need_type,
                'date': datetime.datetime.now(),
                'benefit_id': ids[0] if len(ids) == 1 else '',
                'benefit_ids': [(6, 0, ids)] if len(ids) > 1 else [],
                'f_amount': needs_value,
                'state': 'sent',
                'need_type_ids': [(4, self.product_id.id)] if self.product_id.id else []
            })

    def get_rent(self):
        pass

    # @api.multi
    def print_report(self):
        benefits = []
        needs = []
        family = []
        rooms = []
        columns_ar_headers = []
        columns_headers = []
        if self.service_to == 'benefit':
            if self.benefit_service_category == 'financial':
                columns_ar_headers = ['الاسم', 'العائلة', 'مبلغ الاحتياج', 'نسبة الاحتياج']
                columns_headers = ['name', 'family_id', 'benefit_needs_value', 'benefit_needs_percent']
                for i in self.benefit_f_needs_percent:
                    benefits.append(i.id)
            if self.benefit_service_category == 'In-kind':
                columns_ar_headers = ['الاسم', 'نوع الاحتياج', 'التاريخ', 'نوع المستفيدين', 'حالة الاحتياج', 'الهدف',
                                      'نسبة الاكمال', 'المستفيدين']
                columns_headers = ['name', 'benefit_need_type', 'date', 'benefit_type', 'need_status', 'target_amount',
                                   'completion_ratio', 'benefit_ids']
                for i in self.benefits_need_ids:
                    needs.append(i.id)
            if self.benefit_service_category == 'teaching':
                if self.teaching_type == 'memorization':
                    columns_ar_headers = ['الاسم', 'العائلة', 'حافظ للقران']
                    columns_headers = ['name', 'family_id', 'is_quran_memorize']
                if self.teaching_type == 'specialty':
                    columns_ar_headers = ['الاسم', 'العائلة', 'التخصص']
                    columns_headers = ['name', 'family_id', 'specialization_ids']
                for i in self.benefit_teaching_ids:
                    benefits.append(i.id)
            if self.benefit_service_category == 'qualification':
                if self.qualification_type == 'behavior':
                    columns_ar_headers = ['الاسم', 'النوع', 'العمر', 'السلوك']
                    columns_headers = ['name', 'gender', 'age', 'benefit_behavior_ids']
                if self.qualification_type == 'fat':
                    columns_ar_headers = ['الاسم', 'النوع', 'العمر', 'نسبة الدهون']
                    columns_headers = ['name', 'gender', 'age', 'p_weight']
                for i in self.benefit_qualification_ids:
                    benefits.append(i.id)
            if self.benefit_service_category == 'training':
                columns_ar_headers = ['الاسم', 'النوع', 'العمر', 'التدريب', 'السلوك']
                columns_headers = ['name', 'gender', 'age', 'p_weight', 'benefit_behavior_ids']
            if self.benefit_service_category == 'omra':
                columns_ar_headers = ['الاسم', 'النوع', 'العمر', 'تاريخ اخر عمرة']
                columns_headers = ['name', 'gender', 'age', 'amra_date']
                for i in self.benefit_omra_ids:
                    benefits.append(i.id)
        if self.service_to == 'family':
            if self.service_category == 'financial':
                columns_ar_headers = ['الاسم', 'عدد المستفيدين', 'العائل', 'منتجة ام لا ', 'مجموع الدخل',
                                      'مجموع المصروفات']
                columns_headers = ['name', 'benefits_total', 'responsible_benefit_id', 'is_producer', 'total_income',
                                   'total_expenses']
                for i in self.family_need_ids:
                    family.append(i.id)
            if self.service_category == 'seasonal' and self.seasonal_service_type == 'zkat':
                columns_ar_headers = ['الاسم', 'النوع', 'العمر', 'العائلة']
                columns_headers = ['name', 'gender', 'age', 'family_id']
                for i in self.benefit_ids:
                    benefits.append(i.id)
        if self.service_to == 'house':
            if self.house_service_category == 'fittings':
                columns_ar_headers = ['الوحدة السكنية', 'الغرفة', 'نوع الغرفة', 'المستفيد', 'العمر', 'النوع']
                columns_headers = ['housing_id', 'room_id', 'rooms_categories_id', 'benefit_id', 'age', 'gender']
                for i in self.housing_room_ids:
                    rooms.append(i.id)

        if benefits != [] or needs != [] or family != [] or rooms != [] or columns_ar_headers != [] or columns_headers != []:
            length = len(columns_headers)
            data = {'age_from': self.age_from, 'age_to': self.age_to, 'name': self.name, 'benefits': benefits,
                    'needs': needs,
                    'family': family,
                    'rooms': rooms,
                    'ar_headers': columns_ar_headers,
                    'length': length,
                    'header': columns_headers, }
            pdf = self.env.ref('odex_benefit.generate_benefit_report_pdf')._render_qweb_pdf(self, data=data)
            # b64_pdf = base64.b64encode(pdf[0])
            b64_pdf = base64.b64encode(pdf[0]).decode("ascii")
            # save pdf as attachment
            ir = self.env['ir.attachment'].create({
                'name': self.name if self.name else '' + '.pdf',
                'type': 'binary',
                'datas': b64_pdf,
                # 'datas_fname': self.name + '.pdf',
                'store_fname': self.name,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf'
            })
            self.env['generate.reports.log'].create({
                'name': self.name,
                'user_id': self.current_user.id,
                'datetime': datetime.datetime.now(),
                'attach': b64_pdf
            })
            self.report_file = b64_pdf
            return {'type': 'ir.actions.report', 'report_name': 'odex_benefit.template_generate_benefit_report_pdf',
                    'report_type': "qweb-pdf", 'data': data, }
        else:
            raise ValidationError(_("Sorry, there are no results for this selection !"))

    def rest(self):
        return {
            'name': _('Generate Reports'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'generate.reports',
            'view_id': self.env.ref('odex_benefit.generate_reports_view_form').id,
            'target': 'new',
        }
