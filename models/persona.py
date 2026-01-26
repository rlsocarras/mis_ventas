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
    
    total_deuda_pendiente = fields.Float(
        string='Total Deuda Pendiente',
        compute='_compute_total_deuda',
        store=True
    )


    total_deudas = fields.Float(
        string='Total Deudas',
        compute='_compute_total_compras',
        store=True
    )
    
    @api.depends('deudas_ids.monto_pendiente','deudas_ids.monto_total')
    def _compute_total_deuda(self):
        for persona in self:
            persona.total_deuda_pendiente = sum(
                persona.deudas_ids.mapped('monto_pendiente')
            )
            persona.total_deudas = sum(
                persona.deudas_ids.mapped('monto_total')
            )

    deudas_tags_text = fields.Html(
    compute='_compute_deudas_tags_text',
    string="Deudas como Tags",
    sanitize=False
    )

    def _compute_deudas_tags_text(self):
        for record in self:
            tags = []
            for deuda in record.deudas_ids:
                # Crear HTML que parezca tags
                color = self._get_color_by_estado(deuda.estado)
                tag = f'<span class="badge bg-{color} me-1 text-white">{deuda.display_name_para_personas}</span>'
                tags.append(tag)
        
            record.deudas_tags_text = ''.join(tags) if tags else "Sin deudas"
    
    def _get_color_by_estado(self, estado):
        colores = {
            'pagado': 'success',
            'pendiente': 'danger',
            'vencida': 'warning',
            'parcial': 'info'
        }
        return colores.get(estado, 'secondary')
   