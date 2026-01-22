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
    monto = fields.Float(string='Monto Total', compute='_compute_monto', store=True, readonly=False)
    monto_pagado = fields.Float(string='Monto Pagado', default=0.0)
    monto_pendiente = fields.Float(string='Monto Pendiente', compute='_compute_monto_pendiente', store=True)
    
    fecha = fields.Date(string='Fecha de Deuda', default=fields.Date.today)
    fecha_estimada_pago = fields.Date(string='Fecha Estimada de Pago', 
                                      default=lambda self: fields.Date.today() + timedelta(days=7))
    fecha_pago = fields.Date(string='Fecha de Pago Real')
    
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
    ], string='Estado', default='pendiente')
    
    venta_id = fields.Many2one('ventas.viajes.venta', string='Venta Generada')
    ventas_parciales_ids = fields.One2many('ventas.viajes.venta', 'deuda_parcial_id', 
                                          string='Ventas por Pagos Parciales')
    
    # Campo calculado para mostrar
    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('viaje_id.name','persona_id.nombre', 'producto_id.display_name', 'cantidad', 'monto_pendiente')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Persona - Producto (Cantidad)'"""
        for deuda in self:
            persona_nombre = deuda.persona_id.nombre or 'Sin Persona'
            viaje_nombre = deuda.viaje_id.name or 'Sin Viaje'
            producto_nombre = deuda.producto_id.display_name or 'Sin Producto'
            estado = f"[${deuda.monto_pendiente:.2f} pend.]" if deuda.monto_pendiente > 0 else "[Pagada]"
            deuda.display_name = f"{viaje_nombre} - {persona_nombre} - {producto_nombre} ({deuda.cantidad}) {estado}"
    
    @api.depends('monto', 'monto_pagado')
    def _compute_monto_pendiente(self):
        """Calcula el monto pendiente de pago"""
        for deuda in self:
            deuda.monto_pendiente = deuda.monto - deuda.monto_pagado
    
    @api.depends('monto_pendiente', 'fecha_estimada_pago')
    def _compute_state(self):
        """Calcula el estado automáticamente"""
        today = fields.Date.today()
        for deuda in self:
            if deuda.monto_pendiente <= 0:
                deuda.state = 'pagada'
            elif deuda.monto_pagado > 0:
                deuda.state = 'parcial'
            elif deuda.fecha_estimada_pago and deuda.fecha_estimada_pago < today:
                deuda.state = 'vencida'
            else:
                deuda.state = 'pendiente'
    
    # Restricción: cantidad no puede exceder el disponible
    @api.constrains('cantidad', 'producto_id')
    def _check_cantidad_disponible(self):
        for deuda in self:
            if deuda.producto_id and (deuda.producto_id.cantidad_vendido > deuda.producto_id.cantidad):
                raise models.ValidationError(
                    f'No hay suficiente stock deuda. Solo hay {deuda.producto_id.por_vender} unidades disponibles'
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
            'state': 'borrador',
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

                update_vals['state'] = 'borrador' 
                
                if update_vals:
                    deuda.venta_id.write(update_vals)
        
        return result
    
    def action_pagar_deuda(self):
        """Marcar deuda como pagada completamente y actualizar venta"""
        for deuda in self:
            if deuda.state in ['pagada', 'vencida']:
                continue
                
            # Calcular monto faltante
            monto_faltante = deuda.monto_pendiente
            
            # Actualizar monto pagado
            deuda.monto_pagado += monto_faltante
            deuda.fecha_pago = fields.Date.today()
            
            # Actualizar estado de la deuda
            deuda.state = 'pagada'
            
            # Actualizar venta asociada
            if deuda.venta_id:
                deuda.venta_id.write({
                    'state': 'pagada',
                    'tipo_pago': 'efectivo',
                })
            
            # Crear venta por el pago realizado
            if monto_faltante > 0:
                self._crear_venta_parcial(deuda, monto_faltante, 'Pago completo de deuda')
        
        return True
    
    def action_pago_parcial(self):
        """Abrir wizard para pago parcial"""
        self.ensure_one()
        
        # Si ya está pagada completamente
        if self.monto_pendiente <= 0:
            return {
                'warning': {
                    'title': 'Deuda Pagada',
                    'message': 'Esta deuda ya está completamente pagada.'
                }
            }
        
        # Abrir wizard simple
        return {
            'name': 'Registrar Pago Parcial',
            'type': 'ir.actions.act_window',
            'res_model': 'ventas.viajes.pago.parcial.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deuda_id': self.id,
                'default_monto_maximo': self.monto_pendiente,
                'default_monto': min(100, self.monto_pendiente),  # Sugerir $100 o menos
            }
        }
    
    def _crear_venta_parcial(self, deuda, monto, descripcion):
        """Crear venta por pago parcial"""
        venta_vals = {
            'viaje_id': deuda.viaje_id.id,
            'producto_id': deuda.producto_id.id,
            'cantidad': 1,  # Cantidad simbólica
            'tipo_pago': 'efectivo',
            'monto_total': monto,
            'es_deuda': True,
            'deuda_parcial_id': deuda.id,
            'state': 'pagada',
            'fecha': fields.Date.today(),
            'observaciones': f"Pago parcial de deuda - {descripcion}",
        }
        
        venta = self.env['ventas.viajes.venta'].create(venta_vals)
        return venta
    
    def action_marcar_vencida(self):
        """Marcar deuda como vencida"""
        self.write({'state': 'vencida'})
        return True
    
    def action_reabrir_deuda(self):
        """Reabrir deuda pagada o vencida"""
        self.write({
            'state': 'pendiente',
            'monto_pagado': 0,
            'fecha_pago': False,
        })
        return True