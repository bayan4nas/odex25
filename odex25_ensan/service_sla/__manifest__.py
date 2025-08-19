{
    "name": "Service SLA",
    "version": "14.0.1.0.0",
    "category": "Services",
    "summary": "Add SLA and auto-cancel for service requests",
    "description": "Adds SLA Duration, Deadline, auto-cancel, monitoring and escalation for service requests.",
    "author": "Epert25",
    "depends": ["base", "mail", "trahum_benefits"],
    "data": [
        "data/service_sla_cron.xml",
        "views/benefits_service.xml",
        "views/service_request.xml",
        "views/mail_templates.xml",

    ],
    "installable": True,
    "application": False,
}
