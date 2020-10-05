odoo.define('pos_restaurant.multiprint', function (require) {
"use strict";

var models = require('point_of_sale.models');
var screens = require('point_of_sale.screens');
var core = require('web.core');
var Printer = require('point_of_sale.Printer').Printer;
var pos_restaurant = require('pos_restaurant.multiprint').Printer;

var QWeb = core.qweb;
    models.Orderline = models.Orderline.extend({

    printChanges: async function(){
        var printers = this.pos.printers;
        for(var i = 0; i < printers.length; i++){
            var changes = this.computeChanges(printers[i].config.product_categories_ids);
            var order = this.pos.get_order();
            if ( changes['new'].length > 0 || changes['cancelled'].length > 0){
                var receipt = QWeb.render('OrderChangeReceipt',{changes:changes, widget:this,order:order});
                await printers[i].print_receipt(receipt);
            }
        }
    }
});
