from odoo import models, fields, api

class ViajeProducto(models.Model):
    _name = 'ventas.viaje.producto'
    _description = 'Producto en Viaje'
    _rec_name = 'producto_id'
    
    viaje_id = fields.Many2one(
        'ventas.viaje',
        string='Viaje',
        required=True,
        ondelete='cascade'
    )
    producto_id = fields.Many2one(
        'ventas.producto',
        string='Producto',
        required=True
    )
    cantidad = fields.Integer(string='Cantidad', required=True, default=1)
    precio_compra = fields.Float(string='Precio de Compra', required=True)
    precio_venta = fields.Float(string='Precio de Venta', required=True)
    cantidad_vendido = fields.Integer(
        string='Cantidad Vendida',
        compute='_compute_ventas',
        store=True
    )
    por_vender = fields.Integer(
        string='Por Vender',
        compute='_compute_ventas',
        store=True
    )
    total_invertido = fields.Float(
        string='Total Invertido',
        compute='_compute_totales',
        store=True
    )
    total_ganancia_potencial = fields.Float(
        string='Ganancia Potencial Total',
        compute='_compute_totales',
        store=True
    )
    ganancia_actual = fields.Float(
        string='Ganancia Actual',
        compute='_compute_ventas',
        store=True
    )
    
    # Relación con ventas
    ventas_ids = fields.One2many(
        'ventas.venta',
        'viaje_producto_id',
        string='Ventas'
    )

    deudas_ids = fields.One2many(
        'ventas.deuda',
        'viaje_producto_id',
        string='Deudas'
    )

    @api.depends('cantidad', 'precio_compra', 'precio_venta')
    def _compute_totales(self):
        for record in self:
            record.total_invertido = record.cantidad * record.precio_compra
            record.total_ganancia_potencial = record.cantidad * (
                record.precio_venta - record.precio_compra
            )

    @api.depends('ventas_ids', 'cantidad', 'deudas_ids.cantidad')
    def _compute_ventas(self):
       
        for record in self:
           
            ventas = record.ventas_ids
            deudas = record.deudas_ids
            record.cantidad_vendido = sum(ventas.mapped('cantidad')) +sum(deudas.mapped('cantidad'))
            record.por_vender = record.cantidad - record.cantidad_vendido
            
            # Ganancia actual de ventas realizadas
            ganancia = 0
            for venta in ventas:
                ganancia += venta.cantidad * (
                    record.precio_venta - record.precio_compra
                )
            record.ganancia_actual = ganancia