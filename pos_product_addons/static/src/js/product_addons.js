odoo.define('pos_product_addons.point_of_sale', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');

    models.load_fields('product.product', ['addon_ids', 'has_addons']);

    var _super_pos = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        get_addon_list: function (product_id) {
            // Calls once clicks on the product and shows its add-ons.
            var self = this;
            $('.addon-contents').empty();
            var product = self.db.get_product_by_id(product_id);
            var element = [];
            if (product.addon_ids.length) {
                var $addonpane = $('.addonpane');
                $('.layout-table').css("width", "80%");
                $addonpane.css("visibility", "visible");
                $addonpane.css("width", "13.1%");
                $('.pos .searchbox').css("right", '168px');
                var display_name = '('+product.display_name+')'
                $('.sub-head').text(display_name).show('fast');
                for (var item = 0; item < product.addon_ids.length; item++) {
                    var product_obj = self.db.get_product_by_id([product.addon_ids[item]]);
                    if (product_obj) {
                        element = product_obj.display_name;
                        $('.addons-table').append(
                            '<tr class="addon-contents" class="row" style="width: 100%;">' +
                            '<td class="addons-item" style="width: 100%;" data-addon-id=' + product_obj.id + '> ' +
                            '<div style="display: inline-block; width: 80%;">' + element + '</div>' +
                            '</div></td>' +
                            '</tr>');
                    }
                }
            } else {
                self.hide_addons()
            }

        },
        hide_addons: function () {
            var $layout_table = $('.layout-table');
            $layout_table.removeAttr("width");
            $layout_table.css("width", "100%");
            $('.addonpane').css("visibility", "hidden");
            $('.pos .searchbox').css("right", '0%');
        }
    });
    screens.ProductListWidget.include({

        init: function (parent, options) {
            this._super(parent, options);
            var self = this;
            this.click_product_handler = function () {
                var product_id = this.dataset.productId;
                var product = self.pos.db.get_product_by_id(product_id);
                console.log(self);
                self.pos.get_addon_list(product_id);
                options.click_product_action(product);
            }

        },

    });
    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function (attr, options) {
            _super_orderline.initialize.call(this, attr, options);
            this.addon_items = this.addon_items || [];
        },

        init_from_JSON: function (json) {
            _super_orderline.init_from_JSON.apply(this, arguments);
            this.addon_items = json.addon_items || [];
        },
        export_as_JSON: function () {
            var json = _super_orderline.export_as_JSON.apply(this, arguments);
            json.addon_items = this.addon_items || [];
            return json;
        },
        can_be_merged_with: function (orderline) {
            if (orderline.product.has_addon) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this, arguments);
            }
        },
        //used to create a json of the ticket, to be sent to the printer
        export_for_printing: function(){
            return {
                quantity:           this.get_quantity(),
                unit_name:          this.get_unit().name,
                price:              this.get_unit_display_price(),
                discount:           this.get_discount(),
                product_name:       this.get_product().display_name,
                product_name_wrapped: this.generate_wrapped_product_name(),
                price_lst:          this.get_lst_price(),
                display_discount_policy:    this.display_discount_policy(),
                price_display_one:  this.get_display_price_one(),
                price_display :     this.get_display_price(),
                price_with_tax :    this.get_price_with_tax(),
                price_without_tax:  this.get_price_without_tax(),
                price_with_tax_before_discount:  this.get_price_with_tax_before_discount(),
                tax:                this.get_tax(),
                product_description:      this.get_product().description,
                product_description_sale: this.get_product().description_sale,
                orderline_id :          this.id,
            };
        },
        get_addon_uom: function (id) {
            for (var i = 0; i <= this.addon_items.length; i++) {
                if (this.addon_items[i]['addon_id'] == id) {
                    return this.addon_items[i]['addon_uom']
                }
            }

        }
    });

    screens.ProductScreenWidget.include({
        events: {
            'click .addons-item': 'add_to_orderline',
        },
        add_to_orderline: function (e) {
            var self = this;
            var order = self.pos.get('selectedOrder');
            var $target = $(e.currentTarget);
            var addon_id = $target.data('addon-id');
            var addon_obj = self.pos.db.get_product_by_id([addon_id]);
            var selected_line = order.selected_orderline;
            if (!selected_line) {
                alert('You have to select the corresponding product fist');

            } else {
                var total_price = 0.00;
                for (var i = 0; i < selected_line.product.addon_ids.length; i++) {
                    if (addon_obj.id == selected_line.product.addon_ids[i]) {
                        total_price += addon_obj.lst_price; // Change the value of the price


                    }
                }
                console.log(('wwwwwwww', order))
                order.selected_orderline.price += total_price;
                order.selected_orderline.trigger('change', order.selected_orderline);
                var addons = order.selected_orderline.addon_items;
                var has_already = false;
                for (var i = 0; i < addons.length; i++) {
                    if (addons[i]['addon_id'] == addon_obj.id) {
                        has_already = true;
                        addons[i]['addon_count'] += 1
                    }
                }
                addons.push(
                    {
                        'addon_id': addon_obj.id,
                        'addon_name': addon_obj.display_name,
                        'addon_price': addon_obj.lst_price,
                        'addon_uom': addon_obj.uom_id[1],
                        'addon_count': addon_obj.uom_id[1],
                    }
                );
                order.selected_orderline.trigger('change', order.selected_orderline);
            }
        },

    });

    screens.OrderWidget.include({
        init: function (parent, options) {
            var self = this;
            this._super(parent, options);
            this.line_click_handler = function (event) {
                self.pos.get_addon_list(this.orderline.product.id);
                self.click_line(this.orderline, event);
            };
        },
        orderline_remove: function(line){
        this.remove_orderline(line);
        this.pos.hide_addons();
        this.numpad_state.reset();
        this.update_summary();
    },
    });

    screens.ReceiptScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            this.$('.next').click(function () {
                if (!self._locked) {
                    self.click_next();
                    self.pos.hide_addons()

                }
            });
        },
    });
})
;
