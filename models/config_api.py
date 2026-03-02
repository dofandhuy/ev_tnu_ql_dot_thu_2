# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ConfigAPI(models.Model):
    _inherit = 'config.api'

    code = fields.Selection(selection_add=[
        ("/api/v1/qldt/payment", "/api/v1/qldt/payment"),
    ])