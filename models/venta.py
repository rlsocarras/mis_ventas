from odoo import models, fields, api

class Venta(models.Model):
    _name = 'ventas.viajes.venta'
    _description = 'Registro de Venta'
    _rec_name = 'display_name'

    viaje_id = fields.Many2one('ventas.viajes.viaje', string='Viaje', required=True, ondelete='cascade')
    producto_id = fields.Many2one('ventas.viajes.producto', string='Producto', required=True)
    
    cantidad = fields.Integer(string='Cantidad', required=True, default=1)
    tipo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
    ], string='Tipo de Pago', default='efectivo', required=True)
    
    monto_total = fields.Float(string='Monto Total', compute='_compute_monto_total', store=True, readonly=False)
    fecha = fields.Date(string='Fecha', default=fields.Date.today)
    
    # Campos para deuda
    es_deuda = fields.Boolean(string='Es Deuda')
    deuda_id = fields.Many2one('ventas.viajes.deuda', string='Deuda Relacionada')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='confirmada')
    
    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    deuda_parcial_id = fields.Many2one(
        'ventas.viajes.deuda', 
        string='Deuda Parcial Pagada',
        ondelete='set null'
    )

    observaciones = fields.Text(string='Observaciones')

    @api.depends('producto_id.name', 'viaje_id.name', 'viaje_id.fecha')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Viaje-Producto (Fecha)'"""
        for producto in self:
            viaje_nombre = producto.viaje_id.name or 'Sin Viaje'
            viaje_fecha = producto.viaje_id.fecha or ''
            
            # Formatear fecha si existe
            if viaje_fecha:
                fecha_str = fields.Date.to_string(viaje_fecha)
            else:
                fecha_str = ''
            
            # Crear el nombre completo
            nombre_completo = f"{viaje_nombre} - {producto.producto_id.name}"
            if fecha_str:
                nombre_completo += f" ({fecha_str})"
            
            producto.display_name = nombre_completo

    # Restricción: cantidad no puede exceder el disponible
    @api.constrains('cantidad', 'producto_id')
    def _check_cantidad_disponible(self):
        for venta in self:
            if venta.producto_id and (venta.producto_id.cantidad_vendido > venta.producto_id.cantidad):
                raise models.ValidationError(
                    f'No hay suficiente stock venta. Solo hay {venta.producto_id.por_vender} unidades disponibles'
                )
    
    @api.depends('cantidad', 'producto_id.precio_venta')
    def _compute_monto_total(self):
        """Calcula el monto total automáticamente: cantidad × precio_venta"""
        for venta in self:
            if venta.producto_id and venta.cantidad:
                venta.monto_total = venta.cantidad * venta.producto_id.precio_venta
            else:
                venta.monto_total = 0.0
    
    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        """Cuando cambia el producto, actualizar monto"""
        if self.producto_id:
            self._compute_monto_total()
            
            # Verificar stock disponible
            if self.cantidad > self.producto_id.por_vender:
                return {
                    'warning': {
                        'title': 'Stock Insuficiente',
                        'message': f'Solo hay {self.producto_id.por_vender} unidades disponibles. '
                                  f'Cantidad ajustada a {self.producto_id.por_vender}.'
                    }
                }
                self.cantidad = self.producto_id.por_vender
    
    @api.onchange('cantidad')
    def _onchange_cantidad(self):
        """Cuando cambia la cantidad, recalcular monto"""
        self._compute_monto_total()