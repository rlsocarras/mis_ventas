from odoo import models, fields, api

class Viaje(models.Model):
    _name = 'ventas.viajes.viaje'
    _description = 'Viaje de ventas'
    
    name = fields.Char(string='Nombre del Viaje', required=True)
    fecha = fields.Date(string='Fecha', default=fields.Date.today, required=True)
    
    # Campos calculados
    total_invertido = fields.Float(string='Total Invertido', compute='_compute_totales', store=True)
    ganancia_real = fields.Float(string='Ganancia Real', compute='_compute_totales', store=True,
                                 help='Ganancia basada en productos vendidos: Σ(cantidad_vendida × (precio_venta - precio_compra))')
    ganancia_potencial = fields.Float(string='Ganancia Potencial', compute='_compute_totales', store=True,
                                      help='Ventas totales - Inversión total: (efectivo + transferencia + deuda) - total_invertido')
    total_efectivo = fields.Float(string='Total Efectivo', compute='_compute_totales', store=True)
    total_transferencia = fields.Float(string='Total Transferencia', compute='_compute_totales', store=True)
    total_deuda = fields.Float(string='Total Deuda', compute='_compute_totales', store=True)
    total_ventas = fields.Float(string='Total Ventas', compute='_compute_totales', store=True)
    
    # Nuevo campo: porcentaje de ganancia
    porcentaje_ganancia_real = fields.Float(string='% Ganancia Real', compute='_compute_totales', store=True)
    porcentaje_ganancia_potencial = fields.Float(string='% Ganancia Potencial', compute='_compute_totales', store=True)
    
    # Relaciones
    producto_ids = fields.One2many('ventas.viajes.producto', 'viaje_id', string='Productos')
    venta_ids = fields.One2many('ventas.viajes.venta', 'viaje_id', string='Ventas')
    deuda_ids = fields.One2many('ventas.viajes.deuda', 'viaje_id', string='Deudas')
    
    @api.depends('producto_ids', 'venta_ids', 'deuda_ids')
    def _compute_totales(self):
        for viaje in self:
            # 1. TOTAL INVERTIDO = Sumatoria de (cantidad × precio_compra)
            total_invertido = sum(
                producto.cantidad * producto.precio_compra 
                for producto in viaje.producto_ids
            )
            viaje.total_invertido = total_invertido
            
            # 2. VENTAS POR TIPO DE PAGO
            ventas_validas = viaje.venta_ids.filtered(
                lambda v: v.state in ['confirmada', 'pagada']
            )
            
            viaje.total_efectivo = sum(
                ventas_validas.filtered(lambda v: v.tipo_pago == 'efectivo')
                .mapped('monto_total')
            )
            
            viaje.total_transferencia = sum(
                ventas_validas.filtered(lambda v: v.tipo_pago == 'transferencia')
                .mapped('monto_total')
            )
            
            # 3. DEUDAS PENDIENTES
            deudas_pendientes = viaje.deuda_ids.filtered(
                lambda d: d.state == 'pendiente'
            )
            viaje.total_deuda = sum(deudas_pendientes.mapped('monto'))
            
            # 4. TOTAL VENTAS
            viaje.total_ventas = viaje.total_efectivo + viaje.total_transferencia + viaje.total_deuda
            
            # 5. GANANCIA REAL (basada en productos vendidos)
            ganancia_real = 0
            for producto in viaje.producto_ids:
                cantidad_vendida = producto.cantidad_vendido
                margen_unitario = producto.precio_venta - producto.precio_compra
                ganancia_real += cantidad_vendida * margen_unitario
            
            viaje.ganancia_real = ganancia_real
            
            # 6. GANANCIA POTENCIAL (ventas totales - inversión total)
            viaje.ganancia_potencial = viaje.total_ventas - viaje.total_invertido
            
            # 7. PORCENTAJES DE GANANCIA
            if viaje.total_invertido > 0:
                viaje.porcentaje_ganancia_real = (ganancia_real / viaje.total_invertido) * 100
                viaje.porcentaje_ganancia_potencial = (viaje.ganancia_potencial / viaje.total_invertido) * 100
            else:
                viaje.porcentaje_ganancia_real = 0
                viaje.porcentaje_ganancia_potencial = 0
    
    
    def action_compute_totals(self):
        """Forzar recálculo de totales"""
        self._compute_totales()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Totales recalculados',
                'message': 'Los totales se han actualizado correctamente.',
                'type': 'success',
                'sticky': False,
            }
        }