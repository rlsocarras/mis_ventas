from odoo import models, fields, api
from datetime import date

class Venta(models.Model):
    _name = 'ventas.venta'
    _description = 'Venta'
    _order = 'fecha_venta desc'
    _rec_name = 'display_name'

    viaje_id = fields.Many2one(
        'ventas.viaje',
        string='Viaje',
        required=True,
        ondelete='cascade'
    )
    viaje_producto_id = fields.Many2one(
        'ventas.viaje.producto',
        string='Producto del Viaje',
        required=True,
        domain="[('viaje_id', '=', viaje_id)]"
    )
    producto_id = fields.Many2one(
        'ventas.producto',
        string='Producto',
        related='viaje_producto_id.producto_id',
        store=True,
        readonly=True
    )
    cantidad = fields.Integer(string='Cantidad', required=True, default=1)
    
    precio_unitario = fields.Float(
        string='Precio Unitario',
        related='viaje_producto_id.precio_venta',
        store=True
    )
    total = fields.Float(
        string='Total',
        compute='_compute_total',
        store=True
    )
    ganancia = fields.Float(
        string='Ganancia',
        compute='_compute_ganancia',
        store=True
    )
    tipo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia')
    ], string='Tipo de Pago', required=True, default='efectivo')
    
    # Campos para deudas
    persona_id = fields.Many2one(
        'ventas.persona',
        string='Persona',
    )
    fecha_estimada_pago = fields.Date(string='Fecha Estimada de Pago')
    deuda_id = fields.Many2one(
        'ventas.deuda',
        string='Deuda Asociada',
        readonly=True
    )
    
    fecha_venta = fields.Datetime(
        string='Fecha de Venta',
        default=fields.Datetime.now
    )
    
    estado = fields.Selection([
        ('pagado', 'Pagado'),
        ('deuda', 'Deuda'),
        ('parcial', 'Pago Parcial')
    ], string='Estado', compute='_compute_estado', store=True)

    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    tipo_pago_html = fields.Html(
        string='Tipo de Pago',
        compute='_compute_tipo_pago_html',
        store=False,
        sanitize=False
    )
    
    @api.depends('tipo_pago')
    def _compute_tipo_pago_html(self):
        for venta in self:
            if venta.tipo_pago == 'efectivo':
                html = '''
                    <div style="
                        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                        color: white;
                        padding: 4px 12px;
                        border-radius: 15px;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        font-weight: 600;
                        font-size: 12px;
                        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
                    ">
                        <i class="fa fa-money-bill-wave" style="font-size: 11px;"></i>
                        <span>Efectivo</span>
                    </div>
                '''
            else:  # transferencia
                html = '''
                    <div style="
                        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                        color: white;
                        padding: 4px 12px;
                        border-radius: 15px;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        font-weight: 600;
                        font-size: 12px;
                        box-shadow: 0 2px 4px rgba(0, 123, 255, 0.2);
                    ">
                        <i class="fa fa-university" style="font-size: 11px;"></i>
                        <span>Transferencia</span>
                    </div>
                '''
            venta.tipo_pago_html = html

    @api.depends('producto_id.nombre', 'viaje_id.nombre', 'viaje_id.fecha')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Viaje-Producto-Cantidad (Fecha)'"""
        for producto in self:
            viaje_nombre = producto.viaje_id.nombre or 'Sin Viaje'
            viaje_fecha = producto.viaje_id.fecha or ''
            
            # Formatear fecha si existe
            if viaje_fecha:
                fecha_str = fields.Date.to_string(viaje_fecha)
            else:
                fecha_str = ''
            
            # Crear el nombre completo
            nombre_completo = f"{viaje_nombre} - {producto.producto_id.nombre}"
            if fecha_str:
                nombre_completo += f" ({fecha_str})"
            
            producto.display_name = nombre_completo


    @api.depends('cantidad', 'precio_unitario')
    def _compute_total(self):
        for venta in self:
            venta.total = venta.cantidad * venta.precio_unitario

    @api.depends('cantidad', 'viaje_producto_id.precio_compra', 'precio_unitario')
    def _compute_ganancia(self):
        for venta in self:
            precio_compra = venta.viaje_producto_id.precio_compra
            venta.ganancia = venta.cantidad * (venta.precio_unitario - precio_compra)

    @api.depends('tipo_pago')
    def _compute_estado(self):
        for venta in self:
            if venta.tipo_pago == 'deuda':
                venta.estado = 'deuda'
                # Crear registro de deuda automáticamente
                if not venta.deuda_id and venta.persona_id:
                    deuda = self.env['ventas.deuda'].create({
                        'persona_id': venta.persona_id.id,
                        'venta_id': venta.id,
                        'monto_total': venta.total,
                        'monto_pendiente': venta.total,
                        'fecha_estimada_pago': venta.fecha_estimada_pago,
                    })
                    venta.deuda_id = deuda.id
            else:
                venta.estado = 'pagado'

    @api.onchange('tipo_pago')
    def _onchange_tipo_pago(self):
        if self.tipo_pago != 'deuda':
            self.persona_id = False
            self.fecha_estimada_pago = False

   
                
    @api.constrains('fecha_venta', 'viaje_id')
    def _check_fecha_venta_vs_viaje(self):
        for venta in self:
            if venta.fecha_venta and venta.viaje_id.fecha:
                if venta.fecha_venta.date() < venta.viaje_id.fecha:
                    raise models.ValidationError(
                    'La fecha de venta no puede ser anterior a la fecha del viaje'
                    )
                
def write(self, vals):
    # No permitir modificar monto_total si ya hay pagos
    for deuda in self:
        if 'monto_total' in vals and deuda.total_pagado > 0:
            raise models.ValidationError(
                'No se puede modificar el monto total de una deuda que ya tiene pagos registrados'
            )
    return super().write(vals)

@api.constrains('monto', 'deuda_id')
def _check_monto_no_excede_deuda(self):
    for pago in self:
        if pago.monto > pago.deuda_id.monto_pendiente:
            raise models.ValidationError(
                f'El monto del pago ({pago.monto}) excede el monto pendiente '
                f'de la deuda ({pago.deuda_id.monto_pendiente})'
            )
                