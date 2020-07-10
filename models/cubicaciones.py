# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
    total = fields.Float('Total Cubicado', compute='_compute_total')
    aprobada = fields.Boolean('Aprobada')
    nomina = fields.Many2one('nomina.order', string='Nomina')
    proveedor = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    partidas = fields.One2many(comodel_name='cubicacion.order.line',
                               inverse_name='cubicacion_order_id', string='Partidas')



    @api.depends('partidas.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(line.subtotal for line in rec.partidas)


# Clase que representa las partidas
class CubicacionOrderLine(models.Model):
    _name = 'cubicacion.order.line'

    # _sql_constraints = [('seleccion','check(seleccion = false and pagada = true)','Ya esta linea fue pagada')]

    cubicacion_order_id = fields.Many2one('cubicacion.order', )
    seleccion = fields.Boolean('')
    name = fields.Char('Concepto', required=True)
    partida_type = fields.Selection([('suministro', 'Suministro'),
                                     ('m/o', 'M/O'), ('todo_costo', 'Todo costo')],
                                    string='Tipo', required=True)

    partida_subtype_id = fields.Many2one('partida.subtype', string='Subtipo')
    cantidad = fields.Float('Cantidad')
    contract_line_id = fields.Many2one('contratos.order.line', string='Insumo')
    unit_price = fields.Float('Precio unitario')
    subtotal = fields.Float('Monto Bruto', compute='_compute_total')
    # total = fields.Float('A pagar', compute='_compute_total')
    Pagada = fields.Boolean('Pagada')

    @api.depends('cantidad')
    def _compute_total(self):
        for rec in self:
            rec.subtotal = rec.cantidad * rec.unit_price

    @api.depends('cantidad', 'subtotal')
    def _compute_taxes(self):
        for rec in self:
            if rec.cubicacion_order_id.proveedor.company_type == "person":
                rec.ISR = rec.subtotal * 0.02
                rec.OtroImpuesto = rec.subtotal * 0.0161
            else:
                rec.ISR = 0.00
                rec.OtroImpuesto = 0.00

    # @api.depends('subtotal', 'ISR', 'OtroImpuesto')
    # def subtotal_2(self):
    #     for rec in self:
    #         rec.subtotal2 = rec.subtotal - rec.ISR - rec.OtroImpuesto

    # @api.depends('contract_line_id.porcentaje', 'subtotal2')
    # def _compute_retencion(self):
    #     for rec in self:
    #         amount = (rec.contract_line_id.porcentaje / 100) * rec.subtotal2
    #         # print(amount, rec.contract_line_id.Monto)
    #         # if amount >= rec.contract_line_id.Monto:
    #         #     rec.retencion = rec.contract_line_id.Monto
    #         # else:
    #         rec.retencion = amount


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

class pagos_wizzard(models.TransientModel):
    _name = 'pagos.wizzard'

    monto = fields.Float('Monto')
    contrato = fields.Many2one('contratos.order', string='Contrato')
    proveedor = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    insumo = fields.Many2one('contratos.order.line', string='Yipeta')
    insumo2 = fields.Many2one('contratos.order.line', string='Insumo 2')
    cubicacion = fields.Many2one('cubicacion.order', string='cubicacion')
    concepto = fields.Char(string='concepto')



    @api.model
    def default_get(self, fields):
        result = super(pagos_wizzard, self).default_get(fields)
        if self._context.get('active_id'):
            cubicacion = self.env['cubicacion.order'].browse([self._context.get('active_id')])
            monto = 0
            for rec in cubicacion.partidas:
                if (rec.seleccion and not rec.Pagada):
                    monto = rec.subtotal + monto
            result['monto'] = monto
            result['proveedor'] = cubicacion.proveedor.id
            result['contrato'] = cubicacion.contract_id.id
            result['cubicacion'] = cubicacion.id
        return result

    @api.multi
    def crearPago(self):
        pago = self.env['pagos.order']
        Impuesto1 = 0
        Impuesto2 = 0
        if self.proveedor.company_type == "person":
            Impuesto1 = self.monto * 0.02
            Impuesto2 = self.monto * 0.0161
        MontosDespuesDeImpuestos = self.monto - (Impuesto1 + Impuesto2)


        Intercambio = 0


        if self.insumo:
            temp = self.insumo.porcentaje/100
            Intercambio = temp * MontosDespuesDeImpuestos
            Resta = self.insumo.precio_unitario - self.insumo.adeudado
            print(Resta)
            print(Intercambio)
            if Intercambio >= Resta:
                Intercambio = Resta

        MontoDef = MontosDespuesDeImpuestos - Intercambio
        print(MontoDef)

        Intercambio2 = 0

        if self.insumo2:
            temp = self.insumo2.porcentaje / 100

            Intercambio2 = temp * MontoDef
            Resta = self.insumo2.precio_unitario - self.insumo2.adeudado
            print(Resta)
            print(Intercambio2)
            if Intercambio2 >= Resta:
                Intercambio2 = Resta

        MontoDef = MontoDef - Intercambio2







        pago_nuevo = pago.create({'concepto': self.concepto, 'proveedor': self.proveedor.id,
                     # 'contract_line_id': self.insumo.id,
                     'contract_line_id2': self.insumo2.id,'Monto': self.monto,
                     'Impuesto1': Impuesto1,'Impuesto2': Impuesto2, 'MontoDespuesDeImpuestos': MontosDespuesDeImpuestos,
                     'RetencionIntercambio': Intercambio,'RetencionIntercambio2': Intercambio2, 'MontoDefinitivo': MontoDef})
        for line in self.cubicacion.partidas:
            if(line.seleccion and not line.Pagada):
                line.Pagada = True
        for line in self.contrato.contrato_lines:
            line.pago_id = pago_nuevo.id





class pagos(models.Model):
    _name = 'pagos.order'

    concepto = fields.Char('Concepto', required=True)
    proveedor = fields.Many2one('res.partner', string='Proveedor', domain=[('supplier', '=', True)])
    # contract_line_id = fields.Many2one('contratos.order.line', string='Insumo')
    contract_line_id = fields.One2many('contratos.order.line', 'pago_id', string='Insumo')
    contract_line_id2 = fields.Many2one('contratos.order.line', string='Insumo2')
    # La sumatoria de todas las lineas que seleccione en las cubicaciones
    Monto = fields.Float('Monto')

    # Al monto que recibimos arriba le sacamos las deducciones de ley
    Impuesto1 = fields.Float('ISR', compute='_compute_taxes')
    Impuesto2 = fields.Float('AS', compute='_compute_taxes')

    # Guardamos en una variable lo que queda despues de hacer todas las deducciones de los impuestos
    MontoDespuesDeImpuestos = fields.Float('Despues De Impuestos')

    # Variable final en la que se hacen todos los calculos de los impuestos
    RetencionIntercambio = fields.Float('Intercambio Yipeta')
    RetencionIntercambio2 = fields.Float('Avance Efectivo')

    # Al monto neto le calculamos el porcentaje de la cuota de intercambio y lo guardamos en una variable
    MontoDefinitivo = fields.Float('Al proveedor')

    ## Aqui hacemos el calculo de cada una de las variables

    #Calculo de impuestos
    @api.depends('Monto')
    def _compute_taxes(self):
        for rec in self:
            if rec.proveedor.company_type == "person":
                rec.Impuesto1 = rec.Monto * 0.02
                rec.Impuesto2 = rec.Monto * 0.0161
            else:
                rec.ISR = 0.00
                rec.OtroImpuesto = 0.00

    # Si no hay contrato pues
    # MontoAPagar = MontoDespuesDeImpuestos

    # Si hay un contrato vinculado preguntamos la cuota del insumo
    # CuotaDeRetencionDeContrato = MontoDespuesDeImpuestos * PorcentajeDeLaLineaDeContrato

    # Ahora seleccionamos si queremos hacer una retencion del contrato vinvulado en la cubicacion
    # MontoAPagar = MontoAPagar - CuotaDeRetencionDeContrato




class linea_contrato(models.Model):
    _name = 'contratos.order.line'

    name = fields.Char('Nombre', required=True)
    Tipo = fields.Selection([('avance', 'Avance Efectivo'),
                                     ('intercambio', 'Intercambio')], string='Tipo', required=True)
    avance = fields.Float('Avance')

    cubicaciones_lines_ids = fields.One2many('cubicacion.order.line', 'contract_line_id')
    porcentaje = fields.Float('Porcentaje')
    Producto = fields.Many2one('product.product')
    precio_unitario = fields.Float('Precio unitario', compute='_compute_total')
    adeudado = fields.Float('Pagado', compute='compute_adeudado')

    pago_id = fields.Many2one('pagos.order', string='Pago')

    Monto = fields.Float('Monto', compute='_compute_total')
    contrato_id = fields.Many2one('contratos.order', 'Contrato')

    @api.depends('pago_id', 'Tipo', 'pago_id.RetencionIntercambio2', 'pago_id.RetencionIntercambio')
    def compute_adeudado(self):
        for rec in self:
            # temp = 0
            if rec.Tipo == 'intercambio':
                print('intercambio', rec.pago_id)
                print(rec.pago_id.mapped('RetencionIntercambio'))
                rec.adeudado = sum([pago.RetencionIntercambio for pago in rec.pago_id])
            else:
                print('avance', rec.pago_id)
                print(rec.pago_id.mapped('RetencionIntercambio2'))
                rec.adeudado = sum([pago.RetencionIntercambio2 for pago in rec.pago_id])
            #for pago in rec.pagos_ids:
            #    if rec.Tipo == 'intercambio':
            #        rec.adeudado += pago.RetencionIntercambio
            #        print('pago 1 = ', pago.RetencionIntercambio)
            #    else:
            #        rec.adeudado += pago.RetencionIntercambio2
            #        print('pago 2: ', pago.RetencionIntercambio2)

            rec.adeudado

    @api.depends('Tipo', 'avance', 'Producto', 'porcentaje')
    def _compute_total(self):
        for rec in self:
            if rec.Tipo == 'avance':
                rec.Monto = rec.avance
                rec.precio_unitario = rec.avance

            if rec.Tipo == 'intercambio':
                rec.precio_unitario = rec.Producto.list_price or 0.0
                rec.Monto = rec.Producto.list_price