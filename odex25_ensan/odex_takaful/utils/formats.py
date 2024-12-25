# -*- coding: utf-8 -*-
import re

PHONE_FORMAT = re.compile(r'^0*(\d{9})$')
ID_FORMATS = re.compile(r'^0*(\d{10})$')
PHONE_FORMAT_BACKEND = re.compile(r'^0*(\d{14})$')
MOBILE_FORMAT = re.compile(r'^(\d{8})$')
MOBILE_FORMAT_BACKEND = re.compile(r'^(\d{14})$')
EMAIL_FORMAT = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
ID_FORMAT = re.compile(r'^.+$')
# IBAN_FORMAT = re.compile(r'^[a-zA-Z]{2}[0-9]{2}[a-zA-Z0-9]{4}[0-9]{7}([a-zA-Z0-9]?){0,16}$')
IBAN_FORMAT = re.compile(r'^(\d{22})$')
PASSWORD_FORMAT = re.compile(r'^(?=.*[A-Zء-يa-z])(?=.*\d)[A-Zء-يa-z\d]{6,}$')