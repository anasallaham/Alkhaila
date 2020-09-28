odoo.define('hw_restaurant_ip_printer.printer', function (require) {
"use strict";

    var Printers = require('point_of_sale.Printer')
    var session = require('web.session');


    Printers.Printer.include({
        /**
         * Sends the printing command to the connected network printer
         * @param {String} img : The receipt to be printed, as an image
         */
        send_printing_job: function (img) {

            if(this.config){
                var params = {}
                var k = this.config.proxy_ip;
                params.ip = k.trim() !== "" ? k.split(":").slice(0,1)[0] : '127.0.0.1'
                params.port = (k.indexOf(":") > 0 && k.split(":").slice(-1)[0] !== "") ? k.split(":").slice(-1)[0] : '9100'
                params.receipt = img
                return session.rpc('/hw_net_printer/print_img_receipt', params || {}, {shadow: true})
            }else{
                return this._super(img)
            }
        },
    });
});
