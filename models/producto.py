from odoo import models, fields, api

class Producto(models.Model):
    _name = 'ventas.producto'
    _description = 'Producto'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    descripcion = fields.Text(string='Descripción')
    
    # Relaciones
    viaje_producto_ids = fields.One2many(
        'ventas.viaje.producto',
        'producto_id',
        string='En Viajes'
    )

    # Nuevas relaciones para acceder directamente a ventas y deudas
    ventas_ids = fields.One2many(
        'ventas.venta', 
        'producto_id', 
        string='Ventas de este producto'
    )
    
    deudas_ids = fields.One2many(
        'ventas.deuda', 
        'producto_id', 
        string='Deudas con este producto'
    )
    
    # Campos calculados para estadísticas rápidas
    total_ventas = fields.Integer(
        string='Total Vendido',
        compute='_compute_totales_producto',
        store=False
    )
    
    total_deudas_pendientes = fields.Integer(
        string='Deudas Pendientes',
        compute='_compute_totales_producto',
        store=False
    )
    
    def _compute_totales_producto(self):
        for producto in self:
            # Contar ventas
            producto.total_ventas = len(producto.ventas_ids)
            
            # Contar deudas pendientes (filtrando por estado)
            producto.total_deudas_pendientes = len(
                producto.deudas_ids.filtered(lambda d: d.estado == 'pendiente')
            )