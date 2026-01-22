from odoo import models, fields, api
from datetime import timedelta

class Deuda(models.Model):
    _name = 'ventas.viajes.deuda'
    _description = 'Registro de Deuda'
    _rec_name = 'display_name'
    
    persona_id = fields.Many2one('ventas.viajes.persona', string='Persona', required=True)
    viaje_id = fields.Many2one('ventas.viajes.viaje', string='Viaje', required=True)
    producto_id = fields.Many2one('ventas.viajes.producto', string='Producto', required=True)
    
    cantidad = fields.Integer(string='Cantidad', required=True, default=1)
    monto = fields.Float(string='Monto', compute='_compute_monto', store=True, readonly=False)
    fecha = fields.Date(string='Fecha de Deuda', default=fields.Date.today)
    fecha_estimada_pago = fields.Date(string='Fecha Estimada de Pago', 
                                      default=lambda self: fields.Date.today() + timedelta(days=7))
    fecha_pago = fields.Date(string='Fecha de Pago Real')
    
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ], string='Estado', default='pendiente')
    
    venta_id = fields.Many2one('ventas.viajes.venta', string='Venta Generada')

    # Campo calculado para mostrar
    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('viaje_id.name','persona_id.nombre', 'producto_id.display_name', 'cantidad')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Persona - Producto (Cantidad)'"""
        for deuda in self:
            persona_nombre = deuda.persona_id.nombre or 'Sin Persona'
            viaje_nombre = deuda.viaje_id.name or 'Sin Viaje'
            producto_nombre = deuda.producto_id.display_name or 'Sin Producto'
            deuda.display_name = f"{viaje_nombre} -{persona_nombre} - {producto_nombre} ({deuda.cantidad})"
    
    # Restricción: cantidad no puede exceder el disponible
    @api.constrains('cantidad', 'producto_id')
    def _check_cantidad_disponible(self):
        for deuda in self:
            if deuda.producto_id and (deuda.producto_id.cantidad_vendido > deuda.producto_id.cantidad):
                raise models.ValidationError(
                    f'No hay suficiente stock. Solo hay {deuda.producto_id.por_vender} unidades disponibles'
                )
    
    @api.depends('cantidad', 'producto_id.precio_venta')
    def _compute_monto(self):
        """Calcula el monto automáticamente: cantidad × precio_venta"""
        for deuda in self:
            if deuda.producto_id and deuda.cantidad:
                deuda.monto = deuda.cantidad * deuda.producto_id.precio_venta
            else:
                deuda.monto = 0.0
    
    @api.onchange('producto_id')
    def _onchange_producto_id(self):
        """Cuando cambia el producto, actualizar precio y verificar stock"""
        if self.producto_id:
            # Calcular monto automáticamente
            self._compute_monto()
            
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
        self._compute_monto()
    
    @api.model
    def create(self, vals):
        """Al crear deuda, crear automáticamente la venta asociada"""
        deuda = super(Deuda, self).create(vals)
        
        # Crear venta asociada automáticamente
        venta_vals = {
            'viaje_id': deuda.viaje_id.id,
            'producto_id': deuda.producto_id.id,
            'cantidad': deuda.cantidad,
            'tipo_pago': 'efectivo',  # Se actualizará cuando se pague
            'monto_total': deuda.monto,
            'es_deuda': True,
            'deuda_id': deuda.id,
            'state': 'confirmada',
            'fecha': deuda.fecha,
        }
        venta = self.env['ventas.viajes.venta'].create(venta_vals)
        deuda.venta_id = venta.id
        
        return deuda
    
    def write(self, vals):
        """Al actualizar deuda, actualizar la venta asociada"""
        # Guardar valores anteriores para comparación
        old_cantidad = {d.id: d.cantidad for d in self}
        old_producto = {d.id: d.producto_id.id for d in self}
        
        result = super(Deuda, self).write(vals)
        
        # Actualizar venta asociada si cambió cantidad o producto
        for deuda in self:
            if deuda.venta_id:
                update_vals = {}
                
                if 'cantidad' in vals and vals['cantidad'] != old_cantidad.get(deuda.id):
                    update_vals['cantidad'] = deuda.cantidad
                    update_vals['monto_total'] = deuda.monto
                
                if 'producto_id' in vals and vals['producto_id'] != old_producto.get(deuda.id):
                    update_vals['producto_id'] = deuda.producto_id.id
                    update_vals['monto_total'] = deuda.monto
                
                if update_vals:
                    deuda.venta_id.write(update_vals)
        
        return result
    
    def action_pagar_deuda(self):
        """Marcar deuda como pagada y actualizar venta"""
        for deuda in self:
            if deuda.state != 'pendiente':
                continue
                
            # Actualizar estado de la deuda
            deuda.write({
                'state': 'pagada',
                'fecha_pago': fields.Date.today(),
            })
            
            # Actualizar venta asociada
            if deuda.venta_id:
                deuda.venta_id.write({
                    'state': 'pagada',
                    'tipo_pago': 'efectivo',  # Puedes cambiar esto según cómo se pague
                })
        
        return True
    
    def action_marcar_vencida(self):
        """Marcar deuda como vencida"""
        self.write({'state': 'vencida'})
        return True
    
    def action_reabrir_deuda(self):
        """Reabrir deuda pagada o vencida"""
        self.write({'state': 'pendiente'})
        return True