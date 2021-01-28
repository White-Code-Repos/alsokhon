odoo.define('pos_unfixed.pos', function(require){
    var screens = require('point_of_sale.screens');
    var core = require('web.core');
    var gui = require('point_of_sale.gui');
    var models = require('point_of_sale.models');
    var PopupWidget = require('point_of_sale.popups');
    var QWeb = core.qweb;
    var _t = core._t;

    // var PacklotlineCollection2 = Backbone.Collection.extend({
    //     model: models.Packlotline,
    //     initialize: function(models, options) {
    //         this.order_line = options.order_line;
    //     },
    //
    //     get_empty_model: function(){
    //         return this.findWhere({'lot_name': null});
    //     },
    //
    //     remove_empty_model: function(){
    //         this.remove(this.where({'lot_name': null}));
    //     },
    //
    //     get_valid_lots: function(){
    //         return this.filter(function(model){
    //             return model.get('lot_name');
    //         });
    //     },
    //
    //     set_quantity_by_lot: function() {
    //         if (this.order_line.product.tracking == 'serial' || this.order_line.product.tracking == 'lot') {
    //             var valid_lots = this.get_valid_lots();
    //             this.order_line.set_quantity(valid_lots.length);
    //         }
    //     }
    // });
    // models.load_fields('product.product',['making_charge_id']);
    // models.load_models({
    //     model: 'stock.production.lot',
    //     fields: [],
    //     domain: function(self){
    //         var from = moment(new Date()).subtract(self.config.lot_expire_days,'d').format('YYYY-MM-DD')+" 00:00:00";
    //         if(self.config.allow_pos_lot){
    //             return [['create_date','>=',from]];
    //         }
    //         else{
    //             return [['id','=',0]];
    //         }
    //     },
    //     loaded: function(self,list_lot_num){
    //         self.list_lot_num = list_lot_num;
    //     },
    // });
    var OrderlineSuper = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr,options) {
    			var self = this;
          this.is_unfixed = false;
    			this.purity = false;
    			OrderlineSuper.initialize.call(this,attr,options);
    		},

        export_for_printing: function(){
            var data = OrderlineSuper.export_for_printing.apply(this, arguments);
            data.is_unfixed = this.is_unfixed|| false;
            return data;
        },
        init_from_JSON: function(json) {
            OrderlineSuper.init_from_JSON.apply(this,arguments);
            this.is_unfixed = json.is_unfixed;
        },
        export_as_JSON: function() {
          var loaded = OrderlineSuper.export_as_JSON.apply(this, arguments);
          loaded.is_unfixed = this.is_unfixed || false;
          // this.order_type = 'retail';
          return loaded;
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
    });


    var posorder_super = models.Order.prototype;
  	models.Order = models.Order.extend({
  		initialize: function(attr,options) {
  			var self = this;
        this.order_type = 'retail';
  			this.order_fixed = true;
  			posorder_super.initialize.call(this,attr,options);
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
      // add_product: function(product, options){
      //     posorder_super.add_product.call(this,product,options);
      //
      //
      //
          // if(options.is_unfixed){
          //   line.is_unfixed=true;
          // }else {
          //   line.is_unfixed=false;
          // }
      //
      //
      //
      //     if(line.has_product_lot){
      //         this.display_lot_popup();
      //     }
      //     if (this.pos.config.iface_customer_facing_display) {
      //         this.pos.send_current_order_to_customer_facing_display();
      //     }
      // },
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



    var saleButton = screens.ActionButtonWidget.extend({
    	template: 'saleButton',
    	button_click: function(){
        var self = this;
        var order = this.pos.get_order();
        order.order_type = 'sale';
        $(".wSale_bt").css({'background': '#6EC89B'});
        $(".retail_bt").css({'background':'fixed'});
        $(".fixed_bt").css({'display':'inline-block'});
        $(".unfixed_bt").css({'display':'inline-block'});
    	},
    });
    screens.define_action_button({
    	'name': 'saleorderType',
    	'widget': saleButton,
    });
    var retailButton = screens.ActionButtonWidget.extend({
    	template: 'retailButton',
    	button_click: function(){
        var self = this;
        var order = this.pos.get_order();
        order.order_type = 'retail';
        $(".retail_bt").css({'background': '#6EC89B'});
        $(".wSale_bt").css({'background':'fixed'});
        $(".fixed_bt").css({'display':'none'});
        $(".unfixed_bt").css({'display':'none'});
        $(".unfixed_product").css({'display':'none'});

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
    	'name': 'retailorderType',
    	'widget': retailButton,
    });

    var fixedButton = screens.ActionButtonWidget.extend({
    	template: 'fixedButton',
    	button_click: function(){
        var self = this;
        var order = this.pos.get_order();
        order.order_fixed = true;
        $(".fixed_bt").css({'background': '#a0efc7'});
        $(".unfixed_bt").css({'background':'fixed'});
        $(".unfixed_product").css({'display':'none'});
        $(".add_product").css({'display':'none'});
    	},
    });
    screens.define_action_button({
    	'name': 'fixedType',
    	'widget': fixedButton,
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
        $(".add_product").css({'display':'block'});
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


    //
    // var PackLotLinePopupWidget = PopupWidget.extend({
    //     template: 'PackLotLinePopupWidget',
    //     events: _.extend({}, PopupWidget.prototype.events, {
    //         'click .remove-lot': 'remove_lot',
    //         'keydown': 'add_lot',
    //         'blur .packlot-line-input': 'lose_input_focus'
    //     }),
    //
    //         show: function(options){
    //             var self = this;
    //             var product_lot = [];
    //             var lot_list = self.pos.list_lot_num;
    //             for(var i=0;i<lot_list.length;i++){
    //                 if(lot_list[i].product_id[0] == options.pack_lot_lines.order_line.product.id){
    //                     product_lot.push(lot_list[i]);
    //                 }
    //             }
    //             options.qstr = "";
    //             options.product_lot = product_lot;
    //             this._super(options);
    //             this.focus();
    //         },
    //
    //         renderElement:function(){
    //             this._super();
    //             var self = this;
    //             $.fn.setCursorToTextEnd = function() {
    //                 $initialVal = this.val();
    //                 this.val($initialVal + ' ');
    //                 this.val($initialVal);
    //                 };
    //             $(".search_lot").focus();
    //             $(".search_lot").setCursorToTextEnd();
    //
    //             $(".add_lot_number").click(function(){
    //                 var lot_count = $(this).closest("tr").find("input").val();
    //                 var selling_making_charge= $(this).closest("tr").find("#selling_making_charge")[0].innerText;
    //                 var pure_weight= $(this).closest("tr").find("#pure_weight")[0].innerText;
    //                 var gross_weight= $(this).closest("tr").find("#gross_weight")[0].innerText;
    //                 var purity_id= $(this).closest("tr").find("#purity_id")[0].innerText;
    //                 var gold_rate= $(this).closest("tr").find("#gold_rate")[0].innerText;
    //
    //                 for(var i=0;i<lot_count;i++){
    //                     var lot = $(this).data("lot");
    //
    //                     var input_box;
    //
    //                     $('.packlot-line-input').each(function(index, el){
    //                             input_box = $(el)
    //
    //                     });
    //                     if(input_box != undefined){
    //                         input_box.val(lot);
    //                         var pack_lot_lines = self.options.pack_lot_lines,
    //                             $input = input_box,
    //                             cid = $input.attr('cid'),
    //                             lot_name = $input.val();
    //
    //                         var lot_model = pack_lot_lines.get({cid: cid});
    //
    //                         lot_model.set_lot_name(lot_name);
    //                         if(!pack_lot_lines.get_empty_model()){
    //                             var new_lot_model = lot_model.add();
    //                             self.focus_model = new_lot_model;
    //                         }
    //                         pack_lot_lines.set_quantity_by_lot();
    //                         self.change_price(gold_rate,pure_weight);
    //                         self.renderElement();
    //                         self.focus();
    //                     }
    //                 }
    //             });
    //
    //             $(".search_lot").keyup(function(){
    //                 self.options.qstr = $(this).val();
    //                 var lot_list = self.pos.list_lot_num;
    //                 var product_lot = [];
    //                 for(var i=0;i<lot_list.length;i++){
    //                     if(lot_list[i].product_id[0] == self.options.pack_lot_lines.order_line.product.id && lot_list[i].name.toLowerCase().search($(this).val().toLowerCase()) > -1){
    //                         product_lot.push(lot_list[i]);
    //                     }
    //                 }
    //                 self.options.product_lot = product_lot;
    //                 self.renderElement();
    //
    //             });
    //         },
    //
    //     change_price: function(gold_rate,pure_weight){
    //         var pack_lot_lines = this.options.pack_lot_lines;
    //         this.options.order_line.price=gold_rate*pure_weight;
    //
    //     },
    //
    //
    //     click_confirm: function(){
    //         self = this
    //         var pack_lot_lines = this.options.pack_lot_lines;
    //         this.$('.packlot-line-input').each(function(index, el){
    //             var cid = $(el).attr('cid'),
    //                 lot_name = $(el).val();
    //             var pack_line = pack_lot_lines.get({cid: cid});
    //             pack_line.set_lot_name(lot_name);
    //
    //         });
    //         // selected_lot = this.options.order_line.pack_lot_lines.models[0].attributes.lot_name;
    //         // this.options.product_lot.forEach(function(lot) {
    //         //   if (lot.name == selected_lot)
    //         //   {
    //         //     self.change_price(lot.gold_rate,lot.pure_weight)
    //         //   }
    // 				// 	// order_ids.push(order.id)
    // 				// 	// self.pos.db.get_orders_by_id[order.id] = order;
    // 				// });
    //         pack_lot_lines.remove_empty_model();
    //         pack_lot_lines.set_quantity_by_lot();
    //         var selected_lot = this.options.order_line.pack_lot_lines.models[0].attributes.lot_name;
    //         this.options.product_lot.forEach(function(lot) {
    //           if (lot.name == selected_lot)
    //           {
    //             var order_line = self.options.order_line
    //             var product = self.pos.db.get_product_by_id(self.options.order_line.product.making_charge_id[0]);
    //
    //             self.change_price(lot.gold_rate,lot.pure_weight)
    //             // console.log("hjfghf");
    //             // console.log(product);
    //             // console.log(order_line.quantity * lot.gross_weight * lot.selling_making_charge);
    //             self.options.order.add_product(product, {
    //               quantity: 1,
    //               price: order_line.quantity * lot.gross_weight * lot.selling_making_charge,
    //             });
    //           }
    //           // order_ids.push(order.id)
    //           // self.pos.db.get_orders_by_id[order.id] = order;
    //         });
    //
    //
    //         // var selling_making_charge= $(this).closest("tr").find("#selling_making_charge")[0].innerText;
    //         // var pure_weight= $(this).closest("tr").find("#pure_weight")[0].innerText;
    //         // var gross_weight= $(this).closest("tr").find("#gross_weight")[0].innerText;
    //         // var purity_id= $(this).closest("tr").find("#purity_id")[0].innerText;
    //         // var gold_rate= $(this).closest("tr").find("#gold_rate")[0].innerText;
    //         //
    //         // self.change_price(gold_rate,pure_weight);
    //
    //
    //         // this.options.order_line.price=0;
    //
    //         this.options.order.save_to_db();
    //         this.options.order_line.trigger('change', this.options.order_line);
    //         this.gui.close_popup();
    //     },
    //
    //     add_lot: function(ev) {
    //         if (ev.keyCode === $.ui.keyCode.ENTER && this.options.order_line.product.tracking == 'serial'){
    //             var pack_lot_lines = this.options.pack_lot_lines,
    //                 $input = $(ev.target),
    //                 cid = $input.attr('cid'),
    //                 lot_name = $input.val();
    //
    //             var lot_model = pack_lot_lines.get({cid: cid});
    //             lot_model.set_lot_name(lot_name);  // First set current model then add new one
    //             if(!pack_lot_lines.get_empty_model()){
    //                 var new_lot_model = lot_model.add();
    //                 this.focus_model = new_lot_model;
    //             }
    //             pack_lot_lines.set_quantity_by_lot();
    //             this.renderElement();
    //             this.focus();
    //         }
    //     },
    //
    //     remove_lot: function(ev){
    //         var pack_lot_lines = this.options.pack_lot_lines,
    //             $input = $(ev.target).prev(),
    //             cid = $input.attr('cid');
    //         var lot_model = pack_lot_lines.get({cid: cid});
    //         lot_model.remove();
    //         pack_lot_lines.set_quantity_by_lot();
    //         this.renderElement();
    //     },
    //
    //     lose_input_focus: function(ev){
    //         var $input = $(ev.target),
    //             cid = $input.attr('cid');
    //         var lot_model = this.options.pack_lot_lines.get({cid: cid});
    //         lot_model.set_lot_name($input.val());
    //     },
    //
    //     focus: function(){
    //         this.$("input[autofocus]").focus();
    //         this.focus_model = false;   // after focus clear focus_model on widget
    //     }
    // });
    // gui.define_popup({name:'packlotline', widget:PackLotLinePopupWidget});
});
