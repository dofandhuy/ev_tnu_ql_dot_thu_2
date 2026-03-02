from odoo import models, fields

class HpThanhToanSinhVien(models.Model):
    _name = 'hp.thanh.toan.sinh.vien'
    _description = 'Thanh toán sinh viên (Local)'

    partner_id = fields.Many2one('res.partner', string='Sinh viên')
    unit_id = fields.Many2one('res.business.unit', string='Đơn vị')
    ngay_thanh_toan = fields.Date(string='Ngày thanh toán')
    ct_tt_ids = fields.One2many('hp.tt.sv.chi.tiet', 'parent_id', string='Chi tiết thanh toán')

class HpTtSvChiTiet(models.Model):
    _name = 'hp.tt.sv.chi.tiet'
    _description = 'Chi tiết thanh toán (Local)'

    parent_id = fields.Many2one('hp.thanh.toan.sinh.vien')
    dot_thu_id = fields.Char('Đợt thu')
    product_id = fields.Many2one('product.product', string='Khoản thu')
    so_tien = fields.Float(string='Số tiền')