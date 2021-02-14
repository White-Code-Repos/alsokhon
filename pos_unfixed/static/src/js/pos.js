odoo.define('pos_unfixed.pos', function(require){
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var PopupWidget = require('point_of_sale.popups');
    var utils = require('web.utils');
    var QWeb = core.qweb;
    var _t = core._t;
    var round_di = utils.round_decimals;
  	var round_pr = utils.round_precision;

    screens.OrderWidget.include({


      update_summary: function(){
          var order = this.pos.get_order();
          if (!order.get_orderlines().length) {
              return;
          }

          var total     = order ? order.get_total_with_tax() : 0;
          var taxes     = order ? total - order.get_total_without_tax() : 0;
          var qty_gm = order && order.get_qty_gm_total()?order.get_qty_gm_total():0;
          var make_charge_value = order && order.get_make_charge_value_total()?order.get_make_charge_value_total():0;
          // console.log("order.get_total_purity_qty_gm");
          // console.log(order.get_total_purity_qty_gm());
          // console.log(order.get_total_purity_pure_qty_gm());
          if (this.el.querySelector('.summary .total > .value')) {
            this.el.querySelector('.summary .total > .value').textContent = this.format_currency(total);
          }
          if (this.el.querySelector('.summary .total .subentry .value')) {
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes);
          }

  				if(this.el.querySelector('.total_qty_gm .value')){
  				   this.el.querySelector('.total_qty_gm .value').textContent = qty_gm;
      		}
          if(this.el.querySelector('.total_charge .value')){
  				   this.el.querySelector('.total_charge .value').textContent = this.format_currency(make_charge_value);
      		}
      },

    });


    var OrderlineSuper = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options) {
    			var self = this;
          this.is_unfixed = false;
          this.is_make_charge_value = false;
          this.purity = "";
          this.qty_gm = 0;
          this.qty_gm_pure = 0;
          this.make_charge_value = 0;
    			this.product_lot = {};
    			OrderlineSuper.initialize.call(this,attr,options);
    		},
        export_for_printing: function(){
            var data = OrderlineSuper.export_for_printing.apply(this, arguments);
            data.is_unfixed = this.is_unfixed|| false;
            data.is_make_charge_value = this.is_make_charge_value|| false;
            data.qty_gm = this.qty_gm|| 0;
            data.qty_gm_pure = this.qty_gm_pure|| 0;
            data.make_charge_value = this.make_charge_value|| 0;
            data.purity = this.purity|| "";
            return data;
        },
        init_from_JSON: function(json) {
            OrderlineSuper.init_from_JSON.apply(this,arguments);
            this.is_unfixed = json.is_unfixed;
            this.is_make_charge_value = json.is_make_charge_value;
            this.qty_gm = json.qty_gm;
            this.qty_gm_pure = json.qty_gm_pure;
            this.make_charge_value = json.make_charge_value;
            this.purity = json.purity;
            this.product_lot = json.product_lot;
        },
        export_as_JSON: function() {
          var loaded = OrderlineSuper.export_as_JSON.apply(this, arguments);
          loaded.is_unfixed = this.is_unfixed || false;
          loaded.is_make_charge_value = this.is_make_charge_value || false;
          loaded.qty_gm = this.qty_gm || 0;
          loaded.qty_gm_pure = this.qty_gm_pure || 0;
          loaded.make_charge_value = this.make_charge_value || 0;
          loaded.purity = this.purity || "";
          loaded.product_lot = this.product_lot || "";
          // this.order_type = 'retail';
          return loaded;
        },
        set_purity: function(purity){
					this.purity = purity;
          this.trigger('change',this);
				},
        set_qty_gm: function(qty_gm){
					this.qty_gm = qty_gm;
					this.trigger('change',this);
				},
        set_qty_gm_pure: function(qty_gm_pure){
					this.qty_gm_pure = qty_gm_pure;
					this.trigger('change',this);
				},
        set_make_charge_value: function(make_charge_value){
          this.make_charge_value = make_charge_value;
					this.is_make_charge_value = true;
					this.trigger('change',this);
				},
        get_qty_gm_str: function(){
					return this.qty_gm+"";
				},



        get_all_gm_purity: function(){
            var self = this;
            if (self.purity == "") {
              self.set_purity("0")
            }
            return {
                "purity": self.purity,
                "qty_gm": self.qty_gm,
            };
        },

    });
    screens.PaymentScreenWidget.include({
      init: function(parent, options) {
          var self = this;
          // console.log(this._super(parent, options));

          this._super(parent, options);
          // console.log("sadsdad");
          // console.log(this._super(parent, options));

          this.pos.bind('change:selectedOrder',function(){
                  this.renderElement();
                  this.watch_order_changes();
              },this);
          this.watch_order_changes();

          this.inputbuffer = "";
          this.firstinput  = true;
          this.decimal_point = _t.database.parameters.decimal_point;



          //to focus input in lot screen to //__this
          //
          // // This is a keydown handler that prevents backspace from
          // // doing a back navigation. It also makes sure that keys that
          // // do not generate a keypress in Chrom{e,ium} (eg. delete,
          // // backspace, ...) get passed to the keypress handler.
          this.keyboard_keydown_handler = function(event){
              // if (event.keyCode === 8 || event.keyCode === 46) { // Backspace and Delete
              //     event.preventDefault();
              //
              //     // These do not generate keypress events in
              //     // Chrom{e,ium}. Even if they did, we just called
              //     // preventDefault which will cancel any keypress that
              //     // would normally follow. So we call keyboard_handler
              //     // explicitly with this keydown event.
              //     self.keyboard_handler(event);
              // }
          };
          //
          // // This keyboard handler listens for keypress events. It is
          // // also called explicitly to handle some keydown events that
          // // do not generate keypress events.
          this.keyboard_handler = function(event){
              // On mobile Chrome BarcodeEvents relies on an invisible
              // input being filled by a barcode device. Let events go
              // through when this input is focused.
              // if (BarcodeEvents.$barcodeInput && BarcodeEvents.$barcodeInput.is(":focus")) {
              //     return;
              // }
              //
              // var key = '';
              //
              // if (event.type === "keypress") {
              //     if (event.keyCode === 13) { // Enter
              //         self.validate_order();
              //     } else if ( event.keyCode === 190 || // Dot
              //                 event.keyCode === 110 ||  // Decimal point (numpad)
              //                 event.keyCode === 44 ||  // Comma
              //                 event.keyCode === 46 ) {  // Numpad dot
              //         key = self.decimal_point;
              //     } else if (event.keyCode >= 48 && event.keyCode <= 57) { // Numbers
              //         key = '' + (event.keyCode - 48);
              //     } else if (event.keyCode === 45) { // Minus
              //         key = '-';
              //     } else if (event.keyCode === 43) { // Plus
              //         key = '+';
              //     }
              // } else { // keyup/keydown
              //     if (event.keyCode === 46) { // Delete
              //         key = 'CLEAR';
              //     } else if (event.keyCode === 8) { // Backspace
              //         key = 'BACKSPACE';
              //     }
              // }
              //
              // self.payment_input(key);
              // event.preventDefault();
          };

          //__this

          this.pos.bind('change:selectedClient', function() {
              self.customer_changed();
          }, this);
      },

      renderElement: function() {
          var self = this;
          this._super();



          this.$('.unfixed_product').click(function(){
              // console.log("jsdhsajlkdhalksjdh");
              var list = [];
              // console.log(self);
              // console.log(self.pos.db.product_by_id);
              var products = self.pos.db.product_by_id;

              _.each(products, function (product) {
                // console.log(product);
                  if (product.categ.is_scrap) {
                    list.push({label:product.display_name, item:product.id});
                  }
              });
              self.gui.show_popup('selection',{
      					title: 'Unfixed Product',
      					list: list,
      					confirm: function (product_id) {

                  var prod = self.pos.db.get_product_by_id(product_id);
                  var order = self.pos.get_order();

                  // prod.is_unfixed=true;
                  order.add_product(prod,{is_unfixed:true});
                  // order.get_selected_orderline().is_unfixed=true;
                  // console.log(order.get_selected_orderline());

                  // if (prod.tracking!=='none') {
                  //   console.log("sakdljsldk");
                  //
                  //
                  // }
      						// uom_id = {0:line.pos.units_by_id[uom_id].id, 1:line.pos.units_by_id[uom_id].name};
      						// line.set_uom(uom_id);
      						// line.set_unit_price(line.pos.uom_price[line.product.product_tmpl_id].uom_id[uom_id[0]]);
      						// line.price_manually_set = true;
      					},
      				});
          });
          this.$('.convert_to_fixed').click(function(){
              // console.log("jsdhsajlkdhalksjdh");
              // var list = [];
              var order = self.pos.get_order();
              // console.log(self);
              // console.log(self.pos.db.product_by_id);
              // var products = self.pos.db.product_by_id;

              // _.each(products, function (product) {
              //   // console.log(product);
              //     if (product.categ.is_scrap) {
              //       list.push({label:product.display_name, item:product.id});
              //     }
              // });
              // self.gui.show_popup('AddLotWidget');
              self.gui.show_popup('confirm',{
                'title':  _t('Convert All Remaining to fixed?'),
                'body': _t('Do You Need To Convert All Remaining Weight To fixed?'),
                // 'body': body,
                'comment':_t('Convert All Remaining to fixed?'),
                'confirm': function(){
                  console.log("KSLDALKDJALKDWHJDWJDLA");
                  order.covert_order_fixed = true;
                    // self.selected_table.trash();
                },
              });

              // self.gui.show_popup('selection',{
      				// 	title: 'Unfixed Product',
      				// 	list: list,
      				// 	confirm: function (product_id) {
              //
              //     var prod = self.pos.db.get_product_by_id(product_id);
              //     var order = self.pos.get_order();
              //
              //     // prod.is_unfixed=true;
              //     order.add_product(prod,{is_unfixed:true});
              //     // order.get_selected_orderline().is_unfixed=true;
              //     // console.log(order.get_selected_orderline());
              //
              //     // if (prod.tracking!=='none') {
              //     //   console.log("sakdljsldk");
              //     //
              //     //
              //     // }
      				// 		// uom_id = {0:line.pos.units_by_id[uom_id].id, 1:line.pos.units_by_id[uom_id].name};
      				// 		// line.set_uom(uom_id);
      				// 		// line.set_unit_price(line.pos.uom_price[line.product.product_tmpl_id].uom_id[uom_id[0]]);
      				// 		// line.price_manually_set = true;
      				// 	},
      				// });
          });



      },
      click_back: function(){
  			var self  = this;
  			var order = this.pos.get_order();
        var lines = order.get_orderlines();
        var orderlines = []
        // var i = lines.length-1;
        // var m =0;
        // while (lines) {
        //   if(lines[m].is_unfixed){
        //     lines[m].order.remove_orderline(lines[m]);
        //
        //   }
        // }
        order.get_orderlines().forEach(function (line) {
  					if(line.is_unfixed){
              order.remove_orderline(line);
            }
  			});
        // lines.forEach(function (line) {
  			// 		if(!line.is_unfixed){
        //       orderlines.push(line);
        //     }
  			// });
        // order.orderlines = orderlines;
        this._super();

        // order.orderLines
  			// if(order.is_paying_partial)
  			// {
  			// 	self.payment_deleteorder();
  			// }
  			// else{
  			// 	this._super();
  			// }
  		},
      finalize_validation: function() {
        var self = this;
        console.log("SAJDKHWIQDHIWDIQUWDOIWQDWQIDUWQIJWLNDJ");

        var order = this.pos.get_order();
        console.log("ASKMLDASDAWW");
        console.log(order.get_due_converted_fix());
        console.log(order.get_total_with_tax() , order.get_total_paid());


        if (order.get_due_converted_fix()<1){
          self.gui.show_popup('error',{
          	'title': _t('Order Not Paid'),
          	'body': _t('You cannot get the order. select payment method first.'),
          });
        	return;
        }
        this._super();


          var partner_id = order.get_client();
          // if (!partner_id){
    				// self.gui.show_popup('error',{
    				// 	'title': _t('Unknown customer'),
    				// 	'body': _t('You cannot get the order. Select customer first.'),
    				// });
    			// 	return;
    			// }


      },


    });


    var posorder_super = models.Order.prototype;
  	models.Order = models.Order.extend({
  		initialize: function(attr,options) {
  			var self = this;
        this.order_type = 'retail';
        this.order_fixed = true;
  			this.covert_order_fixed = false;
  			posorder_super.initialize.call(this,attr,options);
  		},
      get_make_charge_value_total: function() {
					var make_charge_value = round_pr(this.orderlines.reduce((function(sum, orderLine) {
															return sum + orderLine.make_charge_value;
														}), 0), this.pos.currency.rounding)
					return make_charge_value ;
	    },
      get_qty_gm_total: function() {
					var qty_gm = round_pr(this.orderlines.reduce((function(sum, orderLine) {
															return sum + orderLine.qty_gm;
														}), 0), this.pos.currency.rounding)

					return qty_gm ;
	    },
      get_qty_gm_pure_total: function() {
					var qty_gm = round_pr(this.orderlines.reduce((function(sum, orderLine) {
															return sum + orderLine.qty_gm_pure;
														}), 0), this.pos.currency.rounding)
					return qty_gm ;
	    },
      get_qty_gm_fixed_total: function() {
					var qty_gm = round_pr(this.orderlines.reduce((function(sum, orderLine) {
						// console.log(orderLine);
            if (!orderLine.is_unfixed) {
              sum += orderLine.qty_gm_pure
            }
						return sum ;
					}), 0), this.pos.currency.rounding)
          console.log('get_qty_gm_fixed_total',qty_gm);

					return qty_gm ;
	    },
      get_qty_gm_unfixed_total: function() {
					var qty_gm = round_pr(this.orderlines.reduce((function(sum, orderLine) {
            if (orderLine.is_unfixed) {
              sum += orderLine.qty_gm_pure
            }
						return sum ;
					}), 0), this.pos.currency.rounding)
          console.log('get_qty_gm_unfixed_total',qty_gm);


					return qty_gm ;
	    },
      get_amount_fixed_total: function() {
					var price = round_pr(this.orderlines.reduce((function(sum, orderLine) {
						// console.log(orderLine);
            if (!orderLine.is_unfixed) {
              sum += orderLine.price;
            }
						return sum ;
					}), 0), this.pos.currency.rounding)

					return price ;
	    },
      get_amount_unfixed_total: function() {
					var price = round_pr(this.orderlines.reduce((function(sum, orderLine) {
						// console.log(orderLine);
            if (orderLine.is_unfixed) {
              sum += orderLine.price;
            }
						return sum ;
					}), 0), this.pos.currency.rounding)

					return price ;
	    },
      get_total_purity_qty_gm: function() {
        var list_total = {};
        this.orderlines.forEach(function(line) {
          if (line.purity=="") {
             line.set_purity("0");
           }
           if (!list_total[line.purity]) {
             list_total[line.purity]=0;
           }
           console.log("line.purity",line.purity);
            list_total[line.purity]+=line.qty_gm_pure;
        });
        console.log("get_total_purity_qty_gm",list_total);
				return list_total ;
	    },
      get_total_unfixed_purity_qty_gm: function() {
        var list_total = {};
        this.orderlines.forEach(function(line) {
          if (line.is_unfixed) {
            if (line.purity=="") {
               line.set_purity("0");
             }
             if (!list_total[line.purity]) {
               list_total[line.purity]=0;
             }
             list_total[line.purity]-=line.qty_gm_pure;

           }
        });
        console.log("get_total_unfixed_purity_qty_gm",list_total);
				return list_total ;
	    },
      get_total_unfixed_purity_pure_qty_gm: function() {
        var list_total = [];
        var pos = this.pos;
        if (this.orderlines.models) {
          var order = this.orderlines.models[0].order;

          for (var total_qty in order.get_total_unfixed_purity_qty_gm()) {
              _.each(pos.list_gold_purity, function(purity) {
                if (purity.name==(total_qty).toString()) {
                  var scrap_purity = purity.scrap_purity/1000;
                  var list = {'pure':total_qty,'qty_gross':order.get_total_unfixed_purity_qty_gm()[total_qty]/scrap_purity,'qty_pure':order.get_total_unfixed_purity_qty_gm()[total_qty],'scrap_purity':scrap_purity}
                  list_total.push(list);
                  return true;
                }
              });
          }
        }
        console.log("get_total_unfixed_purity_pure_qty_gm",list_total);
        return list_total ;
      },
      get_total_purity_pure_qty_gm: function() {
        var list_total = [];
        var pos = this.pos;
        if (this.orderlines.models) {
          var order = this.orderlines.models[0].order;

          for (var total_qty in order.get_total_purity_qty_gm()) {
              // var i = Object.keys(order.get_total_purity_qty_gm()).indexOf(total_qty);
              _.each(pos.list_gold_purity, function(purity) {
                if (purity.name==(total_qty).toString()) {
                  console.log();
                  var scrap_purity = purity.scrap_purity/1000;
                  var list = {'pure':total_qty,'qty_gross':order.get_total_purity_qty_gm()[total_qty]/scrap_purity,'qty_pure':order.get_total_purity_qty_gm()[total_qty],'scrap_purity':scrap_purity}
                  list_total.push(list);
                  return true;
                  // break;
                }
              });
          }
        }
        console.log("get_total_purity_pure_qty_gm",list_total);
        return list_total ;
      },
      get_total_purity_convert_qty_gm: function(orderline) {
        var list_total = [];
        var pos = this.pos;

        var lot_purity=[];
        _.each(orderline.product_lot, function(lot) {
          // console.log(lot);
          if (lot.purity_id&&lot.purity_id[1]) {
            lot_purity.push(lot.purity_id[1]);
          }
        });
        var set = new Set(lot_purity);

        lot_purity=[];
        for (let lot of set) {
            lot_purity.push(lot);
        }

        //
        if (this.orderlines.models) {
          var order = this.orderlines.models[0].order;
          var get_total_purity_pure_qty_gm = order.get_total_purity_pure_qty_gm();
          var total_pure = 0;

          _.each(get_total_purity_pure_qty_gm, function(total_qty) {
            total_pure+=total_qty['qty_pure'];
          });

          _.each(lot_purity, function(purity) {
            var scrap = 0;
            _.each(pos.list_gold_purity, function(puri) {
              if (puri.name==(purity).toString()) {
                scrap = puri.scrap_purity/1000;
                return true;
              }
            });
            console.log("((scrap))",total_pure,scrap,(total_pure/scrap),(total_pure/scrap).toFixed(4));
            var list = {'pure':purity,'qty_gross':(total_pure/scrap),'qty_pure':total_pure}
            list_total.push(list);
          });
        }
        console.log("get_total_purity_convert_qty_gm",list_total);
        return list_total ;
      },
      add_product: function(product, options){
          if(this._printed){
              this.destroy();
              return this.pos.get_order().add_product(product, options);
          }

          this.assert_editable();
          options = options || {};
          var attr = JSON.parse(JSON.stringify(product));
          attr.pos = this.pos;
          attr.order = this;
          var line = new models.Orderline({}, {pos: this.pos, order: this, product: product});
          this.fix_tax_included_price(line);

          if(options.extras !== undefined){
              for (var prop in options.extras) {
                  line[prop] = options.extras[prop];
              }
          }

          if(options.quantity !== undefined){
              line.set_quantity(options.quantity);
          }

          if(options.price !== undefined){
              line.set_unit_price(options.price);
              this.fix_tax_included_price(line);
          }

          if(options.lst_price !== undefined){
              line.set_lst_price(options.lst_price);
          }
          if(options.charge !== undefined){
              line.set_make_charge_value(options.charge);
          }

          if(options.discount !== undefined){
              line.set_discount(options.discount);
          }
          if(options.is_unfixed){
            line.is_unfixed=true;
          }else {
            line.is_unfixed=false;
          }

          var to_merge_orderline;
          for (var i = 0; i < this.orderlines.length; i++) {
              if(this.orderlines.at(i).can_be_merged_with(line) && options.merge !== false){
                  to_merge_orderline = this.orderlines.at(i);
              }
          }
          if (to_merge_orderline){
              to_merge_orderline.merge(line);
              this.select_orderline(to_merge_orderline);
          } else {
              this.orderlines.add(line);
              this.select_orderline(this.get_last_orderline());
          }

          if(line.has_product_lot){
              this.display_lot_popup();
          }
          if (this.pos.config.iface_customer_facing_display) {
              this.pos.send_current_order_to_customer_facing_display();
          }
      },

  		export_as_JSON: function(){
  			var loaded = posorder_super.export_as_JSON.apply(this, arguments);
        loaded.order_type = this.order_type || false;
  			loaded.order_fixed = this.order_fixed || false;
        // this.order_type = 'retail';

  			return loaded;
  		},

  		init_from_JSON: function(json){
  			posorder_super.init_from_JSON.apply(this,arguments);
  			// this.order_type = json.order_type;
  		},
      add_paymentline: function(payment_method,unfixed=0,unfixed_gross=0,purity="") {
          this.assert_editable();
          var newPaymentline = new models.Paymentline({},{order: this, payment_method:payment_method, pos: this.pos});
          if(!payment_method.is_cash_count || this.pos.config.iface_precompute_cash){
              newPaymentline.set_amount( this.get_due() );
          };
          if(this.covert_order_fixed){
            newPaymentline.set_order_to_fix(true);
          }

          if (unfixed) {
            console.log("unfixed",unfixed);
            newPaymentline.set_amount_gm(unfixed);
            // newPaymentline.set_payment_status('waiting');
          }
          if (unfixed_gross) {
            console.log("unfixed",unfixed_gross);
            newPaymentline.set_amount_gm_gross(unfixed_gross);
          }
          this.paymentlines.add(newPaymentline);
          console.log(newPaymentline);
          this.select_paymentline(newPaymentline);
      },
      get_change_value: function(paymentline) {
          if (!paymentline) {
              var change = this.get_total_paid() - this.get_total_with_tax();
              if (!this.order_fixed) {
                change = this.get_total_paid()-this.get_make_charge_value_total();
              }
          } else {
              var change = -this.get_total_with_tax();
              if (!this.order_fixed) {
                change = -this.get_make_charge_value_total();
              }
              var lines  = this.paymentlines.models;
              for (var i = 0; i < lines.length; i++) {
                  change += lines[i].get_amount();
                  if (lines[i] === paymentline) {
                      break;
                  }
              }
          }
          return round_pr(change, this.pos.currency.rounding)
      },
      get_change_convert_value: function(paymentline) {
        if (!paymentline) {
            var change = this.get_total_paid() - this.get_total_with_tax();
        } else {
            var change = -this.get_total_with_tax();
            var lines  = this.paymentlines.models;
            for (var i = 0; i < lines.length; i++) {
                change += lines[i].get_amount();
                if (lines[i] === paymentline) {
                    break;
                }
            }
        }
        return round_pr(change, this.pos.currency.rounding)
      },
      get_due: function(paymentline) {
          if (!paymentline) {
              var due = this.get_total_with_tax() - this.get_total_paid();
              if (!this.order_fixed) {
                due = this.get_make_charge_value_total()- this.get_total_paid();
              }
          } else {
              var due = this.get_total_with_tax();
              if (!this.order_fixed) {
                due = this.get_make_charge_value_total();
              }
              var lines = this.paymentlines.models;
              for (var i = 0; i < lines.length; i++) {
                  if (lines[i] === paymentline) {
                      break;
                  } else {
                      due -= lines[i].get_amount();
                  }
              }
          }
          return round_pr(due, this.pos.currency.rounding);
      },

      get_due_converted_fix: function(paymentline) {
          if (!paymentline) {
              var due = this.get_total_with_tax() - this.get_total_paid();
              // if (!this.order_fixed) {
              //   due = this.get_make_charge_value_total()- this.get_total_paid();
              // }
          } else {
              var due = this.get_total_with_tax();
              // if (!this.order_fixed) {
              //   due = this.get_make_charge_value_total();
              // }
              var lines = this.paymentlines.models;
              for (var i = 0; i < lines.length; i++) {
                  if (lines[i] === paymentline) {
                      break;
                  } else {
                      due -= lines[i].get_amount();
                  }
              }
          }
          return round_pr(due, this.pos.currency.rounding);
      },
      get_due_gm: function(paymentline) {
          if (!paymentline) {
              var due_gm = this.get_qty_gm_fixed_total() + this.get_qty_gm_unfixed_total();
          } else {
              var due_gm = this.get_qty_gm_fixed_total();
              var lines = this.paymentlines.models;

              for (var i = 0; i < lines.length; i++) {
                  if (lines[i] === paymentline) {
                      break;
                  } else {
                      due_gm+= lines[i].get_amount_gm();
                  }
              }
          }
          console.log("due_gm",due_gm);
          return round_pr(due_gm, this.pos.currency.rounding);
      },
  	});

    var pospayment_super = models.Paymentline.prototype;
  	models.Paymentline = models.Paymentline.extend({
  		initialize: function(attr,options) {
  			var self = this;
        this.gm_unfixed = 0;
        this.order_to_fix = false;
  			this.gm_unfixed_pure = 0;
        this.purity = "";

  			pospayment_super.initialize.call(this,attr,options);
  		},
      export_as_JSON: function(){
        var loaded = pospayment_super.export_as_JSON.apply(this, arguments);
        loaded.gm_unfixed = this.gm_unfixed || 0;
        loaded.order_to_fix = this.order_to_fix || false;
        loaded.gm_unfixed_pure = this.gm_unfixed_pure || 0;
        loaded.purity = this.purity;

        return loaded;
      },

      init_from_JSON: function(json){
        pospayment_super.init_from_JSON.apply(this,arguments);
        this.gm_unfixed = json.gm_unfixed;
        this.order_to_fix = json.order_to_fix;
        this.gm_unfixed_pure = json.gm_unfixed_pure;
        this.purity = json.purity;

      },
      export_for_printing: function(){
        var data = pospayment_super.export_for_printing.apply(this, arguments);
        data.gm_unfixed = this.gm_unfixed|| 0;
        data.order_to_fix = this.order_to_fix|| false;
        data.gm_unfixed_pure = this.gm_unfixed_pure|| 0;
        data.purity = this.purity|| 0;
        return data;
      },

      get_amount_gm: function(){
          return this.gm_unfixed;
      },
      get_amount_gm_pure: function(){
          return this.gm_unfixed_pure;
      },
      set_amount_gm: function(value){
          this.order.assert_editable();
          this.gm_unfixed = round_di(parseFloat(value) || 0, this.pos.currency.decimals);
          this.pos.send_current_order_to_customer_facing_display();
          this.trigger('change',this);
      },
      set_amount_gm_gross: function(value){
          this.order.assert_editable();
          this.gm_unfixed_pure = round_di(parseFloat(value) || 0, this.pos.currency.decimals);
          this.pos.send_current_order_to_customer_facing_display();
          this.trigger('change',this);
      },
      set_order_to_fix: function(value){
          this.order.assert_editable();
          this.order_to_fix = value ;
          this.pos.send_current_order_to_customer_facing_display();
          this.trigger('change',this);
      },
      get_make_charge_value_total: function() {
					var make_charge_value = round_pr(this.orderlines.reduce((function(sum, orderLine) {
															return sum + orderLine.make_charge_value;
														}), 0), this.pos.currency.rounding)
					return make_charge_value ;
	    },

  	});




    // var TypeButton = screens.ActionButtonWidget.extend({
    // 	template: 'TypeButton',
    //   init: function (parent, options) {
    //       this._super(parent, options);
    //
    //       this.pos.get('orders').bind('add remove change', function () {
    //           this.renderElement();
    //       }, this);
    //
    //       this.pos.bind('change:selectedOrder', function () {
    //           this.renderElement();
    //       }, this);
    //   },
    // 	button_click: function(){
    //     var self = this;
    //     var list = [];
    //     list.push({label:"Retail", item:1});
    //     list.push({label:"Whole Sale", item:2});
    //     var order = this.pos.get_order();
    //     self.gui.show_popup('selection',{
    //       title: 'Order Type',
    //       list: list,
    //       confirm: function (id) {
    //         if(id==1){
    //           order.order_type = 'retail';
    //           $(".unfixed_product").css({'display':'none'});
    //         }else {
    //           order.order_type = 'sale';
    //           $(".unfixed_product").css({'display':'block'});
    //         }
    //         order.trigger('change');
    //       },
    //
    //     });
    //
    // 	},
    //   get_current_type: function () {
    //       var name = _t('Order Type');
    //       var order = this.pos.get_order();
    //
    //       if (order) {
    //           var order_type = order.order_type;
    //
    //           if (order_type=='retail') {
    //               name = "Retail";
    //           }else {
    //             name = 'Whole Sale';
    //           }
    //       }
    //        return name;
    //   },
    // });
    //
    // screens.define_action_button({
    // 	'name': 'orderType',
    // 	'widget': TypeButton,
    // });



    // var saleButton = screens.ActionButtonWidget.extend({
    // 	template: 'saleButton',
    // 	button_click: function(){
    //     var self = this;
    //     var order = this.pos.get_order();
    //     order.order_type = 'sale';
    //     order.order_fixed = true;
    //     $(".wSale_bt").css({'background': '#6EC89B'});
    //     $(".retail_bt").css({'background':'fixed'});
    //     $(".fixed_bt").css({'display':'inline-block'});
    //     $(".unfixed_bt").css({'display':'inline-block'});
    // 	},
    // });
    // screens.define_action_button({
    // 	'name': 'saleorderType',
    // 	'widget': saleButton,
    // });
    // var retailButton = screens.ActionButtonWidget.extend({
    // 	template: 'retailButton',
    // 	button_click: function(){
    //     var self = this;
    //     var order = this.pos.get_order();
    //     order.order_type = 'retail';
    //     order.order_fixed = true;
    //     $(".retail_bt").css({'background': '#6EC89B'});
    //     $(".wSale_bt").css({'background':'fixed'});
    //     $(".fixed_bt").css({'display':'none'});
    //     $(".unfixed_bt").css({'display':'none'});
    //     $(".unfixed_product").css({'display':'none'});
    //     var order = self.pos.get_order();
    //     var all = $('.product');
    //     $.each(all, function(index, value) {
    //       $(value).find('#availqty').css({'display':'block'});
    //     });
    //
    // 	},
    //   // check_type: function () {
    //   //     // var name = _t('Order Type');
    //   //
    //   //     var order = this.pos.get_order();
    //   //     console.log(order);
    //   //
    //   //     if (order.order_type == 'sale') {
    //   //       $(".wSale_bt").css({'background': '#6EC89B'});
    //   //       $(".retail_bt").css({'background':'fixed'});
    //   //     }else {
    //   //       $(".retail_bt").css({'background': '#6EC89B'});
    //   //       $(".wSale_bt").css({'background':'fixed'});
    //   //     }
    //   // },
    // });
    // screens.define_action_button({
    // 	'name': 'retailorderType',
    // 	'widget': retailButton,
    // });

    var fixedButton = screens.ActionButtonWidget.extend({
    	template: 'fixedButton',
    	button_click: function(){
        var self = this;
        var order = this.pos.get_order();
        order.order_fixed = true;
        $(".fixed_bt").css({'background': '#a0efc7'});
        $(".unfixed_bt").css({'background':'fixed'});
        $(".unfixed_product").css({'display':'none'});
        $(".convert_to_fixed").css({'display':'none'});
        $(".add_product").css({'display':'none'});

        var order = self.pos.get_order();
        var all = $('.product');
        $.each(all, function(index, value) {
          $(value).find('#availqty').css({'display':'block'});
        });

        // console.log($('#availqty'));
        // console.log(screens.ProductScreenWidget.find('#availqty'));
    	},
    });
    screens.define_action_button({
    	'name': 'fixedType',
    	'widget': fixedButton,
      'condition': function () {
        console.log(this.pos);
    			return this.pos.config.session_type=='sale';
    	},
    });
    var unfixedButton = screens.ActionButtonWidget.extend({
    	template: 'unfixedButton',
    	button_click: function(){
        var self = this;
        var order = this.pos.get_order();
        order.order_fixed = false;
        $(".unfixed_bt").css({'background': '#a0efc7'});
        $(".fixed_bt").css({'background':'fixed'});
        $(".unfixed_product").css({'display':'block'});
        $(".convert_to_fixed").css({'display':'block'});
        $(".add_product").css({'display':'block'});

        var order = self.pos.get_order();
        var all = $('.product');
        $.each(all, function(index, value) {
          $(value).find('#availqty').css({'display':'none'});
        });
    	},
      // check_type: function () {
      //     // var name = _t('Order Type');
      //
      //     var order = this.pos.get_order();
      //     console.log(order);
      //
      //     if (order.order_type == 'sale') {
      //       $(".wSale_bt").css({'background': '#6EC89B'});
      //       $(".retail_bt").css({'background':'fixed'});
      //     }else {
      //       $(".retail_bt").css({'background': '#6EC89B'});
      //       $(".wSale_bt").css({'background':'fixed'});
      //     }
      // },
    });
    screens.define_action_button({
    	'name': 'unfixedType',
    	'widget': unfixedButton,
      'condition': function () {
    			return this.pos.config.session_type=='sale';
    	},
    });


    var AddLotWidget = PopupWidget.extend({
        template:'AddLotWidget',

        init: function(parent, options){
            this._super(parent, options);

        },
        events: {
            'click .button.cancel':  'click_cancel',
            'click .button.confirm': 'click_confirm',
        },

        click_confirm: function(){



            this.gui.close_popup();

        },
         click_cancel: function(){
            this.gui.close_popup();

        }

    });
    gui.define_popup({name:'AddLotWidget', widget: AddLotWidget});



});
