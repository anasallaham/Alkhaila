odoo.define('hw_escpos_network_printer.printer', function (require) {
"use strict";

    var Printers = require('point_of_sale.Printer')
    var session = require('web.session');


    var Printer = Printers.Printer.include({
        /**
         * Sends the printing command to the connected network printer
         * @param {String} img : The receipt to be printed, as an image
         */
        send_printing_job: function (img) {

            if(this.pos.config.iface_enable_network_printing){
                var params = {}
                params.ip = this.pos.config.iface_network_printer_ip_address
                params.port = this.pos.config.iface_network_printer_port
                params.receipt = img
                return session.rpc('/hw_net_printer/print_img_receipt', params || {}, {shadow: true})
            }else{
                return this.connection.rpc('/hw_proxy/default_printer_action', {
                    data: {
                        action: 'print_receipt',
                        receipt: img,
                    }
                });
            }
        },
    });

});
