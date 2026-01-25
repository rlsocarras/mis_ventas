from odoo import models, fields, api
from datetime import date

class Deuda(models.Model):
    _name = 'ventas.deuda'
    _description = 'Deuda'
    _order = 'fecha_creacion desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    persona_id = fields.Many2one(
        'ventas.persona',
        string='Persona',
        required=True
    )

    viaje_producto_id = fields.Many2one(
        'ventas.viaje.producto',
        string='Producto del Viaje',
        required=True,
        domain="[('viaje_id', '=', viaje_id)]"
    )

    viaje_id = fields.Many2one(
        'ventas.viaje',
        string='Viaje',
        related='viaje_producto_id.viaje_id',
        store=True
    )

    cantidad = fields.Integer(string='Cantidad', required=True, default=1)

    monto_total = fields.Float(
        string='Total',
        compute='_compute_total',
        store=True,
        tracking=True
    )

    monto_pendiente = fields.Float(
        string='Monto Pendiente',
        compute='_compute_pagos',
        store=True
    )

    fecha_creacion = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now
    )
    fecha_estimada_pago = fields.Date(string='Fecha Estimada de Pago', tracking=True)

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagado', 'Pagado'),
        ('vencida', 'Vencida')
    ], string='Estado', default='pendiente', compute='_compute_estado', store=True, tracking=True)
    
    # Pagos parciales
    pagos_ids = fields.One2many(
        'ventas.pago.deuda',
        'deuda_id',
        string='Pagos'
    )
    total_pagado = fields.Float(
        string='Total Pagado',
        compute='_compute_pagos',
        store=True
    )
    
    # Campos calculados
    dias_vencimiento = fields.Integer(
        string='Días de Vencimiento',
        compute='_compute_dias_vencimiento'
    )

    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('cantidad', 'viaje_producto_id')
    def _compute_total(self):
        for deuda in self:
            deuda.monto_total = deuda.cantidad * deuda.viaje_producto_id.precio_venta

    @api.depends('pagos_ids', 'monto_total','pagos_ids.monto')
    def _compute_pagos(self):
        for deuda in self:
            deuda.total_pagado = sum(deuda.pagos_ids.mapped('monto'))
            deuda.monto_pendiente = deuda.monto_total - deuda.total_pagado

    @api.depends('monto_pendiente', 'fecha_estimada_pago')
    def _compute_estado(self):
        hoy = date.today()
        for deuda in self:
            if deuda.monto_pendiente <= 0:
                deuda.estado = 'pagado'
            elif deuda.monto_pendiente < deuda.monto_total:
                deuda.estado = 'parcial'
            elif deuda.fecha_estimada_pago and deuda.fecha_estimada_pago < hoy:
                deuda.estado = 'vencida'
            else:
                deuda.estado = 'pendiente'

    @api.depends('fecha_estimada_pago')
    def _compute_dias_vencimiento(self):
        hoy = date.today()
        for deuda in self:
            if deuda.fecha_estimada_pago:
                delta = deuda.fecha_estimada_pago - hoy
                deuda.dias_vencimiento = delta.days
            else:
                deuda.dias_vencimiento = 0
    
    def action_registrar_pago(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Pago',
            'res_model': 'ventas.pago.deuda',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deuda_id': self.id,
                'default_monto': self.monto_pendiente,
            }
        }
    
    @api.depends( 'viaje_id.nombre', 'monto_total', 'viaje_producto_id')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Viaje-Persona-Producto (monto)'"""
        for deuda in self:
            viaje_nombre = deuda.viaje_id.nombre or 'Sin Viaje'
            persona_nombre = deuda.persona_id.nombre or ''
            producto_nombre = deuda.viaje_producto_id.producto_id.nombre or ''
          
            
            # Crear el nombre completo
            nombre_completo = f"{viaje_nombre} - {persona_nombre}-{producto_nombre}-({deuda.monto_total})"
            
            deuda.display_name = nombre_completo

    @api.constrains('fecha_estimada_pago')
    def _check_fecha_estimada_pago(self):
        for deuda in self:
            if deuda.fecha_estimada_pago:
                hoy = date.today()
                if deuda.fecha_estimada_pago < hoy:
                    raise models.ValidationError(
                        'La fecha estimada de pago no puede ser en el pasado'
                    )
