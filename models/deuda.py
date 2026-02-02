from odoo import models, fields, api
from datetime import date

class Deuda(models.Model):
    _name = 'ventas.deuda'
    _description = 'Deuda'
    _order = 'fecha_creacion desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    persona_id = fields.Many2one(
        'ventas.persona',
        string='Persona',
        required=True
    )

    viaje_producto_id = fields.Many2one(
        'ventas.viaje.producto',
        string='Producto del Viaje',
        required=True,
        domain="[('viaje_id', '=', viaje_id)]"
    )

    viaje_id = fields.Many2one(
        'ventas.viaje',
        string='Viaje',
        related='viaje_producto_id.viaje_id',
        store=True
    )

    producto_id = fields.Many2one(
        'ventas.producto',
        string='Producto',
        related='viaje_producto_id.producto_id',
        store=True,
        readonly=True
    )

    cantidad = fields.Integer(string='Cantidad', required=True, default=1)

    monto_total = fields.Float(
        string='Total',
        compute='_compute_total',
        store=True,
        tracking=True
    )

    monto_pendiente = fields.Float(
        string='Monto Pendiente',
        compute='_compute_pagos',
        store=True
    )

    fecha_creacion = fields.Datetime(
        string='Fecha de Creación',
        default=fields.Datetime.now
    )
    fecha_estimada_pago = fields.Date(string='Fecha Estimada de Pago', tracking=True)

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagado', 'Pagado'),
        ('vencida', 'Vencida')
    ], string='Estado', default='pendiente', compute='_compute_estado', store=True, tracking=True)
    
    # Pagos parciales
    pagos_ids = fields.One2many(
        'ventas.pago.deuda',
        'deuda_id',
        string='Pagos'
    )
    total_pagado = fields.Float(
        string='Total Pagado',
        compute='_compute_pagos',
        store=True
    )
    
    # Campos calculados
    dias_vencimiento = fields.Integer(
        string='Días de Vencimiento',
        compute='_compute_dias_vencimiento'
    )

    display_name = fields.Char(
        string='Nombre Mostrado',
        compute='_compute_display_name',
        store=True
    )

    display_name_para_personas = fields.Char(
        string='Nombre Mostrado para Personas',
        compute='_compute_display_name',
        store=False
    )

    estado_html = fields.Html(
        string='Estado',
        compute='_compute_estado_html',
        store=False,
        sanitize=False
    )
    
    @api.depends('estado', 'monto_pendiente', 'monto_total')
    def _compute_estado_html(self):
        for deuda in self:
            if deuda.estado == 'pendiente':
                html = '''
                    <div style="
                        background-color: red;
                        color: white;
                        padding: 6px 14px;
                        border-radius: 16px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        border: 1px solid #ffeaa7;
                        box-shadow: 0 1px 3px rgba(255, 193, 7, 0.1);
                    ">
                        <i class="fa fa-clock" style="font-size: 12px;"></i>
                        <span>Pendiente</span>
                    </div>
                '''
            
            elif deuda.estado == 'parcial':
                # Calcular porcentaje pagado
                porcentaje = 0
                if deuda.monto_total and deuda.monto_total > 0:
                    monto_pagado = deuda.monto_total - (deuda.monto_pendiente or 0)
                    porcentaje = (monto_pagado / deuda.monto_total) * 100
                
                html = f'''
                    <div style="
                        display: flex;
                        flex-direction: column;
                        gap: 4px;
                        min-width: 120px;
                    ">
                        <div style="
                            background-color: #fff3cd;
                            color: #856404;
                            padding: 4px 12px;
                            border-radius: 12px;
                            display: inline-flex;
                            align-items: center;
                            gap: 6px;
                            font-weight: 600;
                            font-size: 11px;
                            border: 1px solid #ffeaa7;
                        ">
                            <i class="fa fa-percentage" style="font-size: 11px;"></i>
                            <span>Pago Parcial</span>
                        </div>
                        <div style="
                            display: flex;
                            align-items: center;
                            gap: 8px;
                            font-size: 10px;
                            color: #6c757d;
                        ">
                            <div style="
                                flex: 1;
                                height: 6px;
                                background: #e9ecef;
                                border-radius: 3px;
                                overflow: hidden;
                            ">
                                <div style="
                                    width: {porcentaje:.0f}%;
                                    height: 100%;
                                    background: linear-gradient(90deg, #ffc107, #fd7e14);
                                    border-radius: 3px;
                                "></div>
                            </div>
                            <span style="font-weight: 600;">{porcentaje:.0f}%</span>
                        </div>
                    </div>
                '''
            
            elif deuda.estado == 'pagado':
                html = '''
                    <div style="
                        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                        color: white;
                        padding: 6px 14px;
                        border-radius: 16px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        box-shadow: 0 2px 4px rgba(40, 167, 69, 0.2);
                    ">
                        <i class="fa fa-check-circle" style="font-size: 12px;"></i>
                        <span>Pagado</span>
                    </div>
                '''
            
            else:  # vencida
                html = '''
                    <div style="
                        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
                        color: white;
                        padding: 6px 14px;
                        border-radius: 16px;
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        font-weight: 600;
                        font-size: 12px;
                        box-shadow: 0 2px 4px rgba(220, 53, 69, 0.2);
                    ">
                        <i class="fa fa-exclamation-triangle" style="font-size: 12px;"></i>
                        <span>Vencida</span>
                    </div>
                '''
            
            deuda.estado_html = html
    
    # Campo para mostrar días de vencimiento (si tienes fecha_estimada_pago)
    dias_vencimiento_html = fields.Html(
        string='Días',
        compute='_compute_dias_vencimiento_html',
        store=False,
        sanitize=False
    )
    
    @api.depends('fecha_estimada_pago', 'estado')
    def _compute_dias_vencimiento_html(self):
        for deuda in self:
            hoy = date.today()
            dias_texto = ''
            color = '#6c757d'
            bg_color = '#f8f9fa'
            icon = 'fa-calendar'
            
            if deuda.fecha_estimada_pago:
                diferencia = (deuda.fecha_estimada_pago - hoy).days
                
                if diferencia < 0:  # Vencida
                    dias = abs(diferencia)
                    dias_texto = f'{dias} día{"s" if dias != 1 else ""} vencido{"s" if dias != 1 else ""}'
                    color = '#dc3545'
                    bg_color = '#f8d7da'
                    icon = 'fa-exclamation-circle'
                
                elif diferencia == 0:  # Vence hoy
                    dias_texto = 'Vence hoy'
                    color = '#ffc107'
                    bg_color = '#fff3cd'
                    icon = 'fa-exclamation'
                
                elif diferencia <= 7:  # Pronto a vencer
                    dias_texto = f'{diferencia} día{"s" if diferencia != 1 else ""}'
                    color = '#fd7e14'
                    bg_color = '#ffe5d0'
                    icon = 'fa-clock'
                
                else:  # A tiempo
                    dias_texto = f'{diferencia} días'
                    color = '#28a745'
                    bg_color = '#d4edda'
                    icon = 'fa-calendar-check'
            
            if dias_texto:
                html = f'''
                    <div style="
                        background-color: {bg_color};
                        color: {color};
                        padding: 4px 10px;
                        border-radius: 12px;
                        display: inline-flex;
                        align-items: center;
                        gap: 6px;
                        font-weight: 500;
                        font-size: 11px;
                        border: 1px solid {color}30;
                    ">
                        <i class="fa {icon}" style="font-size: 10px;"></i>
                        <span>{dias_texto}</span>
                    </div>
                '''
            else:
                html = '''
                    <div style="
                        color: #6c757d;
                        font-size: 11px;
                        font-style: italic;
                    ">
                        Sin fecha
                    </div>
                '''
            
            deuda.dias_vencimiento_html = html
    
    # Campo combinado: estado + días vencimiento
    estado_completo_html = fields.Html(
        string='Estado Completo',
        compute='_compute_estado_completo_html',
        store=False,
        sanitize=False
    )
    
    @api.depends('estado_html', 'dias_vencimiento_html')
    def _compute_estado_completo_html(self):
        for deuda in self:
            deuda.estado_completo_html = f'''
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <div>{deuda.estado_html or ""}</div>
                    <div>{deuda.dias_vencimiento_html or ""}</div>
                </div>
            '''

    @api.depends('cantidad', 'viaje_producto_id')
    def _compute_total(self):
        for deuda in self:
            deuda.monto_total = deuda.cantidad * deuda.viaje_producto_id.precio_venta

    @api.depends('pagos_ids', 'monto_total','pagos_ids.monto')
    def _compute_pagos(self):
        for deuda in self:
            deuda.total_pagado = sum(deuda.pagos_ids.mapped('monto'))
            deuda.monto_pendiente = deuda.monto_total - deuda.total_pagado

    @api.depends('monto_pendiente', 'fecha_estimada_pago')
    def _compute_estado(self):
        hoy = date.today()
        for deuda in self:
            if deuda.monto_pendiente <= 0:
                deuda.estado = 'pagado'
            elif deuda.monto_pendiente < deuda.monto_total:
                deuda.estado = 'parcial'
            elif deuda.fecha_estimada_pago and deuda.fecha_estimada_pago < hoy:
                deuda.estado = 'vencida'
            else:
                deuda.estado = 'pendiente'

    @api.depends('fecha_estimada_pago')
    def _compute_dias_vencimiento(self):
        hoy = date.today()
        for deuda in self:
            if deuda.fecha_estimada_pago:
                delta = deuda.fecha_estimada_pago - hoy
                deuda.dias_vencimiento = delta.days
            else:
                deuda.dias_vencimiento = 0
    
    def action_registrar_pago(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Registrar Pago',
            'res_model': 'ventas.pago.deuda',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deuda_id': self.id,
                'default_monto': self.monto_pendiente,
            }
        }
    
    @api.depends( 'viaje_id.nombre', 'monto_total', 'viaje_producto_id', 'cantidad')
    def _compute_display_name(self):
        """Calcula el nombre mostrado: 'Viaje-Persona-Producto-cantida_deuda (monto)'"""
        for deuda in self:
            viaje_nombre = deuda.viaje_id.nombre or 'Sin Viaje'
            persona_nombre = deuda.persona_id.nombre or ''
            producto_nombre = deuda.viaje_producto_id.producto_id.nombre or ''
          
            
            # Crear el nombre completo
            nombre_completo = f"{viaje_nombre} - {persona_nombre} - {producto_nombre} - {deuda.cantidad} - ${deuda.monto_total}"
            
            deuda.display_name = nombre_completo
            deuda.display_name_para_personas = f"{viaje_nombre} - {producto_nombre} - {deuda.cantidad} - ${deuda.monto_total}"

    @api.constrains('fecha_estimada_pago')
    def _check_fecha_estimada_pago(self):
        for deuda in self:
            if deuda.fecha_estimada_pago:
                hoy = date.today()
                if deuda.fecha_estimada_pago < hoy:
                    raise models.ValidationError(
                        'La fecha estimada de pago no puede ser en el pasado'
                    )
