odoo.define('hw_escpos_network_printer.screens', function (require) {
"use strict";
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var PosScreenWidgets = require('point_of_sale.screens');
    var PosChromeWidget = require('point_of_sale.chrome');
    var Printer = require('point_of_sale.Printer').Printer;
    var QWeb = core.qweb;


    PosChromeWidget.Chrome.include({
        // This method instantiates all the screens, widgets, etc. 
        build_widgets: function() {
            var self = this
            _.each(this.widgets, function(widget) {
                // display the print icon for salesDetails widget if using network printer. 
                if(widget.name ==='sale_details'){
                    widget.condition = function(){ return self.pos.config.use_proxy || self.pos.config.iface_enable_network_printing; }
                }
            })
            this._super();

        },
    });


    PosScreenWidgets.ReceiptScreenWidget.include({
        print_html: function () {
            var receipt = QWeb.render('OrderReceipt', this.get_receipt_render_env());
            if(this.pos.config.iface_enable_network_printing){
                var printer = new Printer(this.host, this.pos)
                printer.print_receipt(receipt);
            }else{
                this.pos.proxy.printer.print_receipt(receipt);
            }

            this.pos.get_order()._printed = true;
        },
        print: function() {
            if(this.pos.config.iface_enable_network_printing){
                this.network_printer =  new Printer(this.host, this.pos)
                this.print_html();
                this.lock_screen(false);
            }else{
                this._super();
            }
        },
    });

    /* --------- The Sale Details --------- */

    /** Print an overview of todays sales.
     *
     * If the current cashier is a manager all sales of the day will be printed, else only the sales of the current
     * session will be printed.
     */
    PosChromeWidget.SaleDetailsButton.include({
        /** Print an overview of todays sales using the network printer.
         *
         * By default this will print all sales of the day for current PoS config.
         */
        print_sale_details: function () {
            var self = this;
            rpc.query({
                model: 'report.point_of_sale.report_saledetails',
                method: 'get_sale_details',
                args: [false, false, false, [this.pos.pos_session.id]],
            })
                .then(function(result){
                    var env = {
                        widget: new PosBaseWidget(self),
                        company: self.pos.company,
                        pos: self.pos,
                        products: result.products,
                        payments: result.payments,
                        taxes: result.taxes,
                        total_paid: result.total_paid,
                        date: (new Date()).toLocaleString(),
                    };
                    var report = QWeb.render('SaleDetailsReport', env);
                    if(self.pos.config.iface_enable_network_printing){
                        var printer = new Printer(self.host, self.pos)
                        printer.print_receipt(report);
                    }else{
                        self.pos.proxy.printer.print_receipt(report);
                    }
                });
        },
    });
});
