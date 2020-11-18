odoo.define('pos_delivery_type', function (require) {
"use strict";
    var models = require('point_of_sale.models');
    var chrome = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var _t = core._t;
    models.load_models([
        {
            model: 'pos.delivery.type',
            fields: ['id', 'name'],
            domain: function(self){ return [['id','in', self.config.delivery_type_ids]]; },
            loaded: function (self, delivery_type) {
                self.delivery_type = delivery_type;
            },
        }
    ]);
    var OrderSuper = models.Order;
    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            var result = OrderSuper.prototype.initialize.apply(this,arguments);
            this.selected_delivery_type = 0;
            this.selected_delivery_type_name = 0;
            return result;
            
        },
        export_for_printing:function(){
            var json = OrderSuper.prototype.export_for_printing.apply(this,arguments);
            json.pos_delivery_type = this.selected_delivery_type;
            json.selected_delivery_type_name = this.selected_delivery_type_name;
            return json;
        },
        export_as_JSON: function(){
            var json = OrderSuper.prototype.export_as_JSON.apply(this,arguments);
            json.pos_delivery_type = this.selected_delivery_type;
            return json;
        },
    });
    
    var SetDeliveryTypeButton = screens.ActionButtonWidget.extend({
        template: 'SetDeliveryTypeButton',
        init: function (parent, options){
            this._super(parent, options);

            this.pos.get('orders').bind('add remove change', function () {
                this.renderElement();
            }, this);

            this.pos.bind('change:selectedOrder', function () {
                this.renderElement();
            }, this);
        },
        button_click: function () {
            var self = this;
            var pricelists = _.map(self.pos.delivery_type, function (delivery_type) {
                return {
                    label: delivery_type.name,
                    item: delivery_type.id
                };
            });
            self.gui.show_popup('selection',{
                title: _t('Delivery Type'),
                list: pricelists,
                confirm: function (delivery_type) {
                    var order = self.pos.get_order();
                    order.selected_delivery_type = delivery_type;
                    self.renderElement();
                },
                // is_selected: function (delivery) {
                //     return delivery.name === self.pos.get_order().selected_delivery_type.name;
                // }
            });
        },
        get_current_pricelist_name: function () {
            var name = _t('Take Away');
            var order = this.pos.get_order();

            if (order) {
                var selected_delivery_type = order.selected_delivery_type;
                for(var i=0;i<this.pos.delivery_type.length;i++){
                    if(this.pos.delivery_type[i].id == selected_delivery_type)
                    {
                        name = this.pos.delivery_type[i].name;
                        order.selected_delivery_type_name = name;
                    } 
                }
            }

            return name;
        },
    });

    screens.define_action_button({
        'name': 'SetDeliveryTypeButton',
        'widget': SetDeliveryTypeButton,
        'condition': function(){
            return this.pos.config.delivery_type_ids;
        },
    });

});

