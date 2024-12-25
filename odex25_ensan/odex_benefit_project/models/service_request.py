from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta

class ServiceRequestInherit(models.Model):

    _inherit = 'service.request'

    project_id = fields.Many2one('project.project',srting='Project')
    rent_period = fields.Integer('Rent Period')
    project_create = fields.Boolean(string='Project Create?',related='service_cat.project_create')

    def action_accounting_approve(self):
        super(ServiceRequestInherit, self).action_accounting_approve()
        for rec in self:
            if rec.service_cat.project_create:
                project = self.env['project.project'].create(
                    {
                        'name': (_('%s')%rec.service_cat.service_type) +"/"+ rec.family_id.name +"/"+ rec.family_id.code,
                        'partner_id': rec.service_producer_id.id,
                        'beneficiary_id': rec.family_id.partner_id.id,
                        'category_id' : rec.service_cat.category_id.id,
                        'requested_service_amount' : rec.requested_service_amount,
                        'restoration_max_amount' : rec.restoration_max_amount,
                        'has_money_field_is_appearance': rec.has_money_field_is_appearance,
                        'has_money_to_pay_first_payment' : rec.has_money_to_pay_first_payment,
                        'service_type' : rec.service_cat.service_type,
                        'max_complete_building_house_amount' : rec.max_complete_building_house_amount,
                        'has_money_for_payment_is_appearance' : rec.has_money_for_payment_is_appearance,
                        'has_money_for_payment' : rec.has_money_for_payment,
                    }
                )
                rec.project_id = project

    @api.onchange('requested_service_amount', 'benefit_type', 'date', 'service_cat','family_id','device_id','exception_or_steal','home_furnishing_exception','rent_period','has_marriage_course','member_id','home_age')
    def onchange_requested_service_amount(self):
        res = {}
        today = fields.Date.today()
        date_before_year = today - timedelta(days=365)
        date_before_seven_years = today - relativedelta(years=7)
        date_before_three_years = today - relativedelta(years=3)
        date_before_ten_years = today - timedelta(days=3650)
        date_before_month = today - timedelta(days=30)
        for rec in self:
            # Validation for 'member' benefit type
            if rec.benefit_type == 'member' and rec.service_cat.service_type == 'rent':
                max_requested_amount = rec.service_cat.max_amount_for_student
                if rec.requested_service_amount > max_requested_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _("You cannot request more than %s") % max_requested_amount}
                    return res

            # Validation for 'family' benefit type with 'home_maintenance'
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_maintenance':
                max_requested_amount = rec.service_cat.max_maintenance_amount
                if rec.requested_service_amount > max_requested_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _("You cannot request more than %s") % max_requested_amount}
                    return res

                # Prevent multiple 'home_maintenance' requests within the same year
                existing_request_maintenance = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_maintenance'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_maintenance:
                    raise UserError(_("You cannot request this service more than once a year."))
                existing_request_restoration = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(
                        _("You cannot request this service with restoration service in the same year."))
            # Validation for 'family' benefit type with 'home_restoration'
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_restoration':
                # Prevent multiple 'home_maintenance' requests within the same year
                existing_request_restoration = self.search([
                    ('date', '>', date_before_ten_years),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(_("You cannot request this service more than once a ten years."))
                existing_request_maintenance = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_maintenance')
                ], limit=1)
                if existing_request_maintenance:
                    raise UserError(
                        _("You cannot request this service with maintenance service in the same year."))

            # Validation for 'family' benefit type with 'complete_building_house' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'complete_building_house':
                # Check for existing request of the same type
                existing_request = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'complete_building_house'),
                ], limit=1)
                if existing_request:
                    raise UserError(
                        _("You Cannot request this service twice"))
                existing_request_restoration = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'),
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(
                        _("You Cannot request this service and home restoration twice"))
            # Validation for 'family' benefit type with 'electrical_devices' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'electrical_devices':
                # Check for existing request of the same type in seven years and not exception or steal
                existing_request = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'electrical_devices'),
                    ('date', '>', date_before_seven_years),('device_id','=',rec.device_id.id)
                ], limit=1)
                if existing_request and not rec.exception_or_steal:
                    raise UserError(
                        _("You Cannot request this service twice in seven years"))
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'alternative_housing' and not rec.providing_alternative_housing_based_rent:
                if rec.requested_service_amount > rec.service_cat.rent_amount_for_alternative_housing:
                    raise UserError(
                        _("You Cannot request amount more than %s") % rec.service_cat.rent_amount_for_alternative_housing)
                elif rec.rent_period > rec.service_cat.rent_period:
                    raise UserError(
                        _("You Cannot request this service for period more than %s") % rec.service_cat.rent_period)

            # Validation for 'family' benefit type with 'home_furnishing' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_furnishing':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'home_furnishing'),
                    ('date', '>', date_before_three_years),
                    ('id', '!=', self._origin.id),
                ]
                # if self.id:
                #     domain.append(('id', '!=', self.id))  # Exclude current record if already saved

                # Search for existing requests
                existing_requests_within_three_years = self.search(domain)

                # Include current record in the calculation
                total_amount_in_three_years = sum(existing_requests_within_three_years.mapped('requested_service_amount'))
                total_amount_in_three_years += sum(self.furnishing_items_ids.mapped('furnishing_cost'))
                if not rec.home_furnishing_exception:
                    if total_amount_in_three_years > rec.service_cat.max_furnishing_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s within 3 years") % rec.service_cat.max_furnishing_amount}
                        return res
                if rec.home_furnishing_exception:
                    if total_amount_in_three_years > rec.service_cat.max_furnishing_amount_if_exception:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s within 3 years") % rec.service_cat.max_furnishing_amount_if_exception}
                        return res
            # Validation for 'family' benefit type with 'electricity_bill' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'electricity_bill':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'electricity_bill'),
                    ('date', '>', date_before_month),('id', '!=', self._origin.id)
                ]
                # Search for existing requests
                existing_requests_within_month = self.search(domain)
                if existing_requests_within_month:
                    raise UserError(_("You cannot request this service agin in this month"))
                if rec.requested_service_amount > rec.max_electricity_bill_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.max_electricity_bill_amount}
                    return res
            # Validation for 'family' benefit type with 'water_bill' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'water_bill':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'water_bill'),
                    ('date', '>', date_before_year),('id','!=',self._origin.id)
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)
                if existing_requests_within_year:
                    raise UserError(_("You cannot request this service agin in this year"))
                if rec.requested_service_amount > rec.max_water_bill_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.max_water_bill_amount}
                    return res
            # Validation for 'family' benefit type with  'buy_car' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'buy_car':
                if rec.family_id.has_car:
                    raise UserError(_("You cannot request this service because you had a car"))
                if rec.benefit_member_count < rec.service_cat.min_count_member:
                    raise UserError(_("You cannot request this service because you are less than %s")%rec.service_cat.min_count_member)
                if rec.requested_service_amount > rec.service_cat.max_buy_car_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_buy_car_amount}
                    return res
            # Validation for 'family' benefit type with  'recruiting_driver' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'recruiting_driver':
                recruiting_driver_existing_request = self.search([
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'recruiting_driver'), ('id', '!=', self._origin.id)], limit=1)
                son_members_above_age = rec.family_id.mapped('member_ids').filtered(lambda x:x.relationn.relation_type == 'son' and x.age > 18)
                daughter_members_above_age = rec.family_id.mapped('member_ids').filtered(lambda x: x.relationn.relation_type == 'daughter' and x.age > 18)
                disable_mother = rec.family_id.mapped('member_ids').filtered(lambda x: x.relationn.relation_type == 'mother' and x.has_disabilities)
                work_mother = rec.family_id.mapped('member_ids').filtered(lambda x: x.relationn.relation_type == 'mother' and x.is_mother_work)
                disable_replacement_mother = rec.family_id.mapped('member_ids').filtered(lambda x: x.relationn.relation_type == 'replacement_mother' and x.has_disabilities)
                work_replacement_mother = rec.family_id.mapped('member_ids').filtered(lambda x: x.relationn.relation_type == 'replacement_mother' and x.replacement_is_mother_work)
                if not rec.family_id.has_car:
                    raise UserError(_("You cannot request this service because you do not have a car"))
                if son_members_above_age or daughter_members_above_age:
                    raise UserError(
                        _("You cannot request this service because children above 18 years"))
                if rec.family_id.add_replacement_mother and not disable_replacement_mother and not work_replacement_mother :
                    raise UserError(
                        _("You cannot request this service because mother should be worked or has disability"))
                if not rec.family_id.add_replacement_mother and not disable_mother and not work_mother:
                    raise UserError(
                        _("You cannot request this service because mother should be worked or has disability"))
                if recruiting_driver_existing_request:
                    raise UserError(
                        _("You cannot request this service Again"))
                if rec.requested_service_amount > rec.service_cat.max_recruiting_driver_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_recruiting_driver_amount}
                    return res
            # Validation for 'family' benefit type with  'transportation_insurance' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'transportation_insurance':
                if rec.service_reason == 'government_transportation':
                    if rec.requested_service_amount > rec.max_government_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_government_transportation_amount}
                        return res
                if rec.service_reason == 'universities_training_institutes_transportation':
                    if rec.requested_service_amount > rec.max_universities_training_institutes_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_universities_training_institutes_transportation_amount}
                        return res
                if rec.service_reason == 'hospitals_transportation':
                    if rec.requested_service_amount > rec.max_hospitals_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_hospitals_transportation_amount}
                        return res
                if rec.service_reason == 'programs_transportation':
                    if rec.requested_service_amount > rec.max_programs_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_hospitals_transportation_amount}
                        return res
            # Validation for 'family' benefit type with  'recruiting_driver' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'debits':
                if rec.requested_service_amount > rec.service_cat.max_debits_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_debits_amount}
                    return res
            # Validation for 'family' benefit type with  'health_care' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'health_care':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'health_care'),
                    ('date', '>', date_before_year),
                    ('id', '!=', self._origin.id),
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)

                # Include current record in the calculation
                total_amount_in_year = sum(existing_requests_within_year.mapped('requested_service_amount'))
                total_amount_in_year += rec.requested_service_amount
                if total_amount_in_year > rec.service_cat.max_health_care_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s within year") % rec.service_cat.max_health_care_amount}
                    return res
            # Validation for 'family' benefit type with  'health_care' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'recruiting_domestic_worker_or_nurse':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'recruiting_domestic_worker_or_nurse'),
                    ('date', '>', date_before_year),
                    ('id', '!=', self._origin.id),
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)
                if existing_requests_within_year:
                    raise UserError(_("You cannot request this service more than once Within year."))
                # Include current record in the calculation
                if rec.requested_service_amount > rec.service_cat.max_recruiting_domestic_worker_or_nurse_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s within year") % rec.service_cat.max_recruiting_domestic_worker_or_nurse_amount}
                    return res
            # Validation for 'member' benefit type with  'marriage' service type
            if rec.benefit_type == 'member' and rec.service_cat.service_type == 'marriage':
                if rec.member_age > rec.service_cat.member_max_age:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "Member Age should be less than %s ") % rec.service_cat.member_max_age}
                    return res
                if rec.member_payroll > rec.service_cat.member_max_payroll:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "Member Payroll should be less than %s ") % rec.service_cat.member_max_payroll}
                    return res
                if rec.has_marriage_course == 'no':
                    raise UserError(_("You Should take a course"))
            # Validation for 'family' benefit type with  'eid_gift' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'eid_gift':
                if rec.eid_gift_benefit_count == 0:
                    raise UserError(_("You cannot request this service because family should have members his age less than %s")%rec.service_cat.eid_gift_max_age)
            # Validation for 'member' benefit type with  'eid_gift' service type
            if rec.benefit_type == 'member' and rec.service_cat.service_type == 'eid_gift':
                if rec.member_id.age > rec.service_cat.eid_gift_max_age:
                    raise UserError(_("You cannot request this service because your age should be less than %s")%rec.service_cat.eid_gift_max_age)
            # Validation for 'family' benefit type with  'natural_disasters' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'natural_disasters':
                if rec.requested_service_amount > rec.service_cat.natural_disasters_max_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message':_("You cannot request more than %s")  % rec.service_cat.natural_disasters_max_amount}
                    return res
            # Validation for 'family' benefit type with  'legal_arguments' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'legal_arguments':
                if rec.requested_service_amount > rec.service_cat.legal_arguments_max_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _("You cannot request more than %s") % rec.service_cat.legal_arguments_max_amount}
                    return res
            # Validation for 'family' benefit type with  'buy_home' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'buy_home':
                # Search for existing requests
                existing_buy_home_requests = self.search([('family_id', '=', self.family_id.id),
                                                            ('service_cat.service_type', '=','buy_home'),
                                                            ('id', '!=', self._origin.id)])
                existing_home_restoration_requests = self.search([('family_id', '=', self.family_id.id),
                                                         ('service_cat.service_type', '=', 'home_restoration'),
                                                         ('id', '!=', self._origin.id)])
                if rec.requested_service_amount > rec.service_cat.buy_home_max_total_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.buy_home_max_total_amount}
                    return res
                if existing_buy_home_requests:
                    raise UserError(_("You cannot request this service Again"))
                if existing_home_restoration_requests:
                    raise UserError(_("You cannot request this service Again Because you request Home restoration service"))
                if rec.home_age > rec.service_cat.home_age:
                    raise UserError(
                        _("You cannot request this service Again Because the home Age More than %s") % rec.service_cat.home_age)




