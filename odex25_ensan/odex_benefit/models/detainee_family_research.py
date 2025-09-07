from odoo import models, fields, api, _
from random import randint
import logging

from odoo.exceptions import  ValidationError
class DetaineeFamilyResearch(models.Model):
    _name = 'detainee.family.research'
    # _description = 'Detainee Family Research'

    benefit_id = fields.Many2one(
        'grant.benefit',
        string='Family File',
        required=True,
        domain=[('detainee_file_id.beneficiary_category', '=', 'gust')],
        help="Select the family file (search by ID number is available)."
    )
    detainee_id = fields.Many2one(
        'detainee.file', string="Detainee",
    )

    breadwinner_name = fields.Char(
        string='Breadwinner Name',
        related='benefit_id.benefit_breadwinner_ids.member_name.name', store=True, readonly=True)
    breadwinner_id_number = fields.Char(
        string='Breadwinner ID Number',
        related='benefit_id.benefit_breadwinner_ids.member_name.member_id_number', store=True, readonly=True)
    benefit_member_count = fields.Integer(
        string='Family Members Count',
        related='benefit_id.benefit_member_count', store=True, readonly=True)

    detainee_name = fields.Char(
        string='Detainee Name',
        related='detainee_id.name', store=True, readonly=True)

    housing_type = fields.Selection(related="benefit_id.housing_type", string="Housing Type", readonly=True)
    property_type = fields.Selection(related="benefit_id.property_type", string="Property Type", readonly=True)
    housing_status = fields.Selection(
        [
            ('bad', 'Bad'),
            ('good', 'Good'),
            ('excellent', 'Excellent'),
        ],
        string='Housing Condition'
    )

    specialization = fields.Char(string='Specialization')
    is_employee = fields.Boolean(string='Is Employee?')
    experience_years = fields.Integer(string='Years of Experience')
    experience_unit = fields.Selection(
        [('month', 'Month'), ('year', 'Year')],
        string='Experience Unit'
    )

    researcher_report = fields.Text(string='Researcher Report')
    researcher_id = fields.Many2one('committees.line',related='benefit_id.researcher_id', string="Researcher Name")
    researcher_signature = fields.Char(string="Signature")
    specialist_name = fields.Char(string="Specialist Name")
    specialist_signature = fields.Char(string="Signature")
    benefit_service_manager_name = fields.Char(string="Beneficiary Service Manager")
    benefit_service_manager_signature = fields.Char(string="Signature")
    ceo_name = fields.Char(string="CEO")
    ceo_signature = fields.Char(string="Signature")

    create_date = fields.Datetime(string='Creation Date', readonly=True)



    type = fields.Selection(
        string='',
        selection=[('male', 'Men'),
                   ('female', 'women'),
                   ('both', 'combined'),
                   ],
        required=False, )

