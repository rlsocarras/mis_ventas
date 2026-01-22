from odoo import models, fields, api

class Producto(models.Model):
    _name = 'ventas.viajes.producto'
    _description = 'Producto del viaje'
    
    name = fields.Char(string='Nombre del Producto', required=True)
    viaje_id = fields.Many2one('ventas.viajes.viaje', string='Viaje', required=True, ondelete='cascade')
    
    cantidad = fields.Integer(string='Cantidad Total', required=True, default=1)
    precio_compra = fields.Float(string='Precio de Compra', required=True)
    precio_venta = fields.Float(string='Precio de Venta', required=True)
    
    # Campos calculados
    cantidad_vendido = fields.Integer(string='Cantidad Vendido', compute='_compute_ventas', store=True)
    por_vender = fields.Integer(string='Por Vender', compute='_compute_ventas', store=True)
    total_invertido = fields.Float(string='Total Invertido', compute='_compute_totales', store=True)
    total_ganancia = fields.Float(string='Ganancia Total Potencial', compute='_compute_totales', store=True)
    ganancia_actual = fields.Float(string='Ganancia Actual', compute='_compute_totales', store=True)
    
    # Relación con ventas
    venta_ids = fields.One2many('ventas.viajes.venta', 'producto_id', string='Ventas')
    
    @api.depends('venta_ids.cantidad', 'venta_ids.state')
    def _compute_ventas(self):
        for producto in self:
            cantidad_vendida = 0
            for venta in producto.venta_ids:
                if venta.state in ['confirmada', 'pagada']:
                    cantidad_vendida += venta.cantidad
            producto.cantidad_vendido = cantidad_vendida
            producto.por_vender = producto.cantidad - cantidad_vendida
    
    @api.depends('cantidad', 'precio_compra', 'precio_venta', 'cantidad_vendido')
    def _compute_totales(self):
        for producto in self:
            producto.total_invertido = producto.cantidad * producto.precio_compra
            producto.total_ganancia = producto.cantidad * (producto.precio_venta - producto.precio_compra)
            producto.ganancia_actual = producto.cantidad_vendido * (producto.precio_venta - producto.precio_compra)