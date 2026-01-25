from odoo import models, fields, api

class Persona(models.Model):
    _name = 'ventas.persona'
    _description = 'Persona'
    _rec_name = 'nombre'

    nombre = fields.Char(string='Nombre', required=True)
    contacto = fields.Char(string='Contacto')
    
    # Relaciones
    deudas_ids = fields.One2many(
        'ventas.deuda', 
        'persona_id', 
        string='Deudas'
    )
    ventas_ids = fields.One2many(
        'ventas.venta',
        'persona_id',
        string='Ventas a Crédito'
    )
    
    total_deuda = fields.Float(
        string='Total Deuda Pendiente',
        compute='_compute_total_deuda',
        store=True
    )


    total_compras = fields.Float(
        string='Total Compras',
        compute='_compute_total_compras',
        store=True
    )
    
    @api.depends('deudas_ids.monto_pendiente')
    def _compute_total_deuda(self):
        for persona in self:
            persona.total_deuda = sum(
                persona.deudas_ids.mapped('monto_pendiente')
            )
    @api.depends('ventas_ids.total')
    def _compute_total_compras(self):
        for persona in self:
            persona.total_compras = sum(
                persona.ventas_ids.mapped('total')
            )