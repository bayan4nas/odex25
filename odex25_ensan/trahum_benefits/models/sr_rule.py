from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

OPERATORS = [
    ('<', 'Less than'),
    ('<=', 'Less than or equal to'),
    ('==', 'Equal to'),
    ('!=', 'Not equal to'),
    ('>=', 'Greater than or equal to'),
    ('>', 'Greater than'),
]


PERIODS = [
    ('none', 'No Period'),
    ('month', 'Monthly'),
    ('year', 'Yearly'),
    ('days', 'Days'),
    ('custom', 'Custom Period')
]


RULE_TYPES = [
    ('validation', 'شرط'),
    ('compute', 'حساب'),
]

SCOPES = [
    ('request', 'الطلب الحالي'),
    ('beneficiary', 'المستفيد (فرد/أسرة)'),
]

# METRICS = [
#     ('request_total', 'إجمالي الطلب'),
#     ('sum_amount_period', 'مجموع المبالغ للفترة'),
#     ('count_requests_period', 'عدد الطلبات في الفترة'),
#     ('days_since_last_request', 'أيام منذ آخر طلب'),
#     ('family_members_count', 'عدد أفراد الأسرة'),
# ]
METRICS = [
    ('request_total', 'Total Requests'),
    ('sum_amount_period', 'Total Amount in Period'),
    ('count_requests_period', 'Number of Requests in Period'),
    ('days_since_last_request', 'Days Since Last Request'),
    ('family_members_count', 'Family Members Count'),
    ('family_value', 'Family Value'),
    ('tolerance_ratio', 'Tolerance Ratio'),
    ('service_repetition', 'Service Repetition Count'),
    ('housing_support_rule', 'Housing Support Rule'),

]
HOUSING_PROPERTY_TYPES = [
    ('ownership', 'ownership'),
    ('rent', 'rent'),
    ('charitable', 'charitable'),
    ('ownership_shared', 'Ownership Shared'),
    ('rent_shared', 'Rent Shared')
]

HOUSING_EXCHANGE_PERIODS = [
    ('monthly', 'Monthly'),
    ('every_three_months', 'Every Three Months'),
    ('every_six_months', 'Every Six Months'),
    ('every_nine_months', 'Every Nine Months'),
    ('annually', 'Annually'),
    ('two_years', 'Two Years'),
]


class SrRule(models.Model):
    _name = 'sr.rule'
    _description = 'قاعدة طلب الخدمة'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    rule_type = fields.Selection(RULE_TYPES, required=True, default='validation')
    scope = fields.Selection(SCOPES, required=True, default='beneficiary')
    metric = fields.Selection(METRICS, required=True, default='sum_amount_period')

    operator = fields.Selection(OPERATORS, default='<=', help='Comparison')
    threshold_value = fields.Float(string='Threshold Value')
    member_value = fields.Float(string='Member Value')
    breadwinner_value = fields.Float(string='Breadwinner Value')

    period = fields.Selection(PERIODS, default='year')

    severity = fields.Selection([('error', 'Blocker'), ('warning', 'Warning')], default='error')

    message = fields.Char(string='Violation Message')

    numeric_value = fields.Float(string='Tolerance Ratio %')
    date_from = fields.Date(string='From Date')
    date_to = fields.Date(string='To Date')
    housing_property_type = fields.Selection(
        HOUSING_PROPERTY_TYPES,
        string="Target Housing Type"
    )
    housing_exchange_type = fields.Selection(
        HOUSING_EXCHANGE_PERIODS,
        string="EXCHANGE PERIODS"
    )

    period_days = fields.Integer(string='Period in Days')

    one_time_support = fields.Boolean(string='دعم لمرة واحدة',
                                     )

    rent_duration_years = fields.Integer(
        string='Years',
    )

    rent_duration_months = fields.Integer(
        string='Months',
    )

    duration_operator = fields.Selection(
        OPERATORS,
        string='Duration Comparison Operator',
    )

    duration_violation_message = fields.Text(
        string='Rental Duration Violation Message'
    )

    # Second condition - Amount
    max_service_amount = fields.Float(
        string='Reference Amount',
        help='The reference amount used to compare with the service request amount'
    )

    amount_operator = fields.Selection(
        OPERATORS,
        string='Amount Comparison Operator',
        help='The operator applied to the service request amount'
    )

    amount_violation_message = fields.Text(
        string='Service Amount Violation Message'
    )
    allowed_need_categories = fields.Many2many(
        'family.need.category',
        'sr_rule_need_category_rel',
        'rule_id',
        'category_id',
        string='تصنيف الاحتياج المسموح',
    )

    restrict_to_threshold = fields.Boolean(string='Restrict to Threshold', default=False)
    default_member_count = fields.Integer(string='Default Member Count', default=0)
    default_breadwinner_count = fields.Integer(string='Default Breadwinner Count', default=0)