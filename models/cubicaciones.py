# -*- coding: utf-8 -*-

from odoo import models, fields, api


# Clase que representa las cubicaciones
class CubicacionOrder(models.Model):
    _name = 'cubicacion.order'
    _rec_name = 'name'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 default=lambda self: self.env.user.company_id.id)
    date_start = fields.Date('Fecha inicio', required=True)
    date_end = fields.Date('Fecha fin')
    contract_id = fields.Many2one('contratos.order', string='Contrato')
    total = fields.Float('Total a pagar a suplidor', compute='_compute_total')
    aprobada = fields.Boolean('Aprobada')
    nomina = fields.Many2one('nomina.order', string='Nomina')
    proveedor = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])

    partidas = fields.One2many(comodel_name='cubicacion.order.line',
                               inverse_name='cubicacion_order_id', string='Partidas')

    @api.depends('partidas.total')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(line.total for line in rec.partidas)


# Clase que representa las partidas
class CubicacionOrderLine(models.Model):
    _name = 'cubicacion.order.line'

    cubicacion_order_id = fields.Many2one('cubicacion.order', )
    name = fields.Char('Nombre', required=True)
    partida_type = fields.Selection([('suministro', 'Suministro'),
                                     ('m/o', 'M/O'), ('todo_costo', 'Todo costo')],
                                    string='Tipo', required=True)
    partida_subtype_id = fields.Many2one('partida.subtype', string='Subtipo')
    cantidad = fields.Float('Cantidad')

    contract_line_id = fields.Many2one('contratos.order.line', string='Insumo')
    ISR = fields.Float('ISR', compute='_compute_taxes')
    OtroImpuesto = fields.Float('AS', compute='_compute_taxes')

    unit_price = fields.Float('Precio unitario')
    subtotal = fields.Float('Subtotal', compute='_compute_total')
    subtotal2 = fields.Float('Subtotal 2', compute='subtotal_2')
    retencion = fields.Float('Retención', compute='_compute_retencion')

    total = fields.Float('A pagar', compute='_compute_total')

    @api.depends('cantidad', 'subtotal2', 'retencion')
    def _compute_total(self):
        for rec in self:
            if rec.cubicacion_order_id.proveedor.company_type == "person":
                rec.subtotal = rec.cantidad * rec.unit_price
                rec.total = rec.subtotal2 - rec.retencion
            else:
                rec.subtotal = rec.cantidad * rec.unit_price
                rec.total = rec.subtotal2 - rec.retencion

    @api.depends('cantidad', 'subtotal')
    def _compute_taxes(self):
        for rec in self:
            if rec.cubicacion_order_id.proveedor.company_type == "person":
                rec.ISR = rec.subtotal * 0.02
                rec.OtroImpuesto = rec.subtotal * 0.0161
            else:
                rec.ISR = 0.00
                rec.OtroImpuesto = 0.00

    @api.depends('subtotal', 'ISR', 'OtroImpuesto')
    def subtotal_2(self):
        for rec in self:
            rec.subtotal2 = rec.subtotal - rec.ISR - rec.OtroImpuesto

    @api.depends('contract_line_id.porcentaje', 'subtotal2')
    def _compute_retencion(self):
        for rec in self:
            amount = (rec.contract_line_id.porcentaje / 100) * rec.subtotal2
            # print(amount, rec.contract_line_id.Monto)
            # if amount >= rec.contract_line_id.Monto:
            #     rec.retencion = rec.contract_line_id.Monto
            # else:
            rec.retencion = amount


class PartidaSubtipo(models.Model):
    _name = 'partida.subtype'

    name = fields.Char('Nombre', required=True)


class nomina(models.Model):
    _name = 'nomina.order'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 default=lambda self: self.env.user.company_id.id)
    # supplier_id = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])

    date_start = fields.Date('Fecha inicio', required=True)
    date_end = fields.Date('Fecha fin')
    Monto = fields.Float('Total', compute='_compute_total')

    cubicaciones = fields.One2many(comodel_name='cubicacion.order',
                               inverse_name='nomina', string='Cubicaciones')

    @api.depends('cubicaciones.total')
    def _compute_total(self):
        for rec in self:
            rec.Monto = sum(line.total for line in rec.cubicaciones)


class contrato(models.Model):
    _name = 'contratos.order'

    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one('res.company', string='Compañía',
                                 default=lambda self: self.env.user.company_id.id)
    date_start = fields.Date('Fecha inicio', required=True)
    date_end = fields.Date('Fecha fin')
    monto_contrato = fields.Float('Monto contrato')
    monto_faltante = fields.Float('Monto Faltante', compute='_compute_monto_faltante')
    state = fields.Selection([('no_paid', 'No pagado'), ('paid', 'Pagado')], string='Estatus')
    Contratista = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    contrato_lines = fields.One2many('contratos.order.line', inverse_name='contrato_id',
                                     string='Líneas de contrato')

    @api.depends('monto_contrato', 'contrato_lines.Monto')
    def _compute_monto_faltante(self):
        for rec in self:
            rec.monto_faltante = rec.monto_contrato - sum(rec.contrato_lines.mapped('Monto'))


class linea_contrato(models.Model):
    _name = 'contratos.order.line'

    name = fields.Char('Nombre', required=True)
    Tipo = fields.Selection([('avance', 'Avance Efectivo'),
                                     ('intercambio', 'Intercambio'), ('cubicacion', 'Cubicacion')], string='Tipo', required=True)
    avance = fields.Float('Avance')

    cubicaciones_lines_ids = fields.One2many('cubicacion.order.line', 'contract_line_id')
    porcentaje = fields.Float('Porcentaje')
    
    Producto = fields.Many2one('product.product')
    cubicacion = fields.Many2one('cubicacion.order', string='Cubicación')
    precio_unitario = fields.Float('Precio unitario', compute='_compute_total')
    Monto = fields.Float('Monto', compute='_compute_total')
    contrato_id = fields.Many2one('contratos.order', 'Contrato')

    @api.depends('Tipo', 'avance', 'Producto', 'cubicacion', 'porcentaje', 'cubicaciones_lines_ids.retencion')
    def _compute_total(self):
        for rec in self:
            if rec.Tipo == 'avance':
                rec.Monto = rec.avance - (sum(rec.cubicaciones_lines_ids.mapped('retencion')))

            if rec.Tipo == 'intercambio':
                rec.precio_unitario = rec.Producto.list_price or 0.0
                amount = rec.precio_unitario - (sum(rec.cubicaciones_lines_ids.mapped('retencion')))
                if amount < 0.0:
                    amount = 0.0
                rec.Monto = amount

            if rec.Tipo == 'cubicacion':
                rec.Monto = rec.cubicacion.total or 0.0