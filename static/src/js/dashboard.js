// Dashboard interactivo para Ventas Viajes
odoo.define('mis_ventas.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ajax = require('web.ajax');

    var Dashboard = Widget.extend({
        template: 'DashboardTemplate',
        
        init: function (parent, action) {
            this._super(parent);
            this.action = action;
        },
        
        start: function () {
            var self = this;
            return this._super().then(function () {
                // Cargar datos del dashboard
                self._loadDashboardData();
                
                // Configurar eventos
                self._setupEvents();
            });
        },
        
        _loadDashboardData: function () {
            var self = this;
            
            // Aquí puedes cargar datos adicionales vía AJAX si es necesario
            ajax.jsonRpc('/mis_ventas/get_dashboard_data', 'call', {})
                .then(function (data) {
                    // Procesar datos recibidos
                    self._updateDashboard(data);
                })
                .catch(function (error) {
                    console.error('Error cargando datos del dashboard:', error);
                });
        },
        
        _updateDashboard: function (data) {
            // Actualizar elementos del dashboard con los datos recibidos
            // Esta función se puede expandir según necesites
        },
        
        _setupEvents: function () {
            var self = this;
            
            // Hacer las filas de la tabla clickeables
            this.$('.clickable-row').click(function () {
                var href = $(this).data('href');
                if (href) {
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'ventas.viajes.viaje',
                        views: [[false, 'form']],
                        res_id: $(this).data('id'),
                        target: 'current'
                    });
                }
            });
            
            // Botón de recargar datos
            this.$('.reload-dashboard').click(function () {
                self._loadDashboardData();
            });
        }
    });

    // Registrar el dashboard
    core.action_registry.add('ventas_viajes_dashboard', Dashboard);

    return {
        Dashboard: Dashboard,
    };
});