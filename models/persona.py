from odoo import models, fields, api

class Persona(models.Model):
    _name = 'ventas.viajes.persona'
    _description = 'Persona con deuda'
    _rec_name = 'nombre'
    
    nombre = fields.Char(string='Nombre', required=True)
    contacto = fields.Char(string='Contacto')
    deuda_ids = fields.One2many('ventas.viajes.deuda', 'persona_id', string='Deudas')
    total_deuda = fields.Float(string='Total Deuda', compute='_compute_total_deuda', store=True)
    
    @api.depends('deuda_ids.monto', 'deuda_ids.state')
    def _compute_total_deuda(self):
        for persona in self:
            total = 0
            for deuda in persona.deuda_ids:
                if deuda.state == 'pendiente':
                    total += deuda.monto
            persona.total_deuda = total