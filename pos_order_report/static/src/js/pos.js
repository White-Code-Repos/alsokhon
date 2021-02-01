odoo.define('pos_order_report.pos', function(require) {
	"use strict";
	var screens = require('point_of_sale.screens');
	var gui = require('point_of_sale.gui');
	var core = require('web.core');
	var _t = core._t;
	screens.ReceiptScreenWidget.include({
	       events: {
	       'click .order-print': 'orderClickEvent',
	   },
	   orderClickEvent: function(e){
	       var self = this;
	       var order_name = self.pos.get_order().name
	           this._rpc({
	               model: 'pos.order',
	               method: 'print_report',
	               args: [[]],
	           }).then(function (result) {
	               self.do_action(result);
	           });
	   },
	});
});
