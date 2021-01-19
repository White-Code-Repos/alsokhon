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
    // var OrderlineSuper = models.Orderline;
    // models.Orderline = models.Orderline.extend({
    //     set_product_lot: function(product){
    //         this.has_product_lot = product.tracking !== 'none' && this.pos.config.use_existing_lots;
    //         this.pack_lot_lines  = this.has_product_lot && new PacklotlineCollection2(null, {'order_line': this});
    //     },
    //     export_for_printing: function(){
    //         var pack_lot_ids = [];
    //         if (this.has_product_lot){
    //             this.pack_lot_lines.each(_.bind( function(item) {
    //                 return pack_lot_ids.push(item.export_as_JSON());
    //             }, this));
    //         }
    //         var data = OrderlineSuper.prototype.export_for_printing.apply(this, arguments);
    //         data.pack_lot_ids = pack_lot_ids;
    //         return data;
    //     },
    //
    //     get_order_line_lot:function(){
    //         var pack_lot_ids = [];
    //         if (this.has_product_lot){
    //             this.pack_lot_lines.each(_.bind( function(item) {
    //                 return pack_lot_ids.push(item.export_as_JSON());
    //             }, this));
    //         }
    //         return pack_lot_ids;
    //     },
    //     get_required_number_of_lots: function(){
    //         var lots_required = 1;
    //
    //         if (this.product.tracking == 'serial' || this.product.tracking == 'lot') {
    //             lots_required = this.quantity;
    //         }
    //
    //         return lots_required;
    // },
    //
    //
    // });
    screens.PaymentScreenWidget.include({

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
                  console.log(product_id);

                  var prod = self.pos.db.get_product_by_id(product_id);
                  var order = self.pos.get_order();

                  prod.is_unfixed=true;
                  order.add_product(prod);
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
    });


    var posorder_super = models.Order.prototype;
  	models.Order = models.Order.extend({

  		initialize: function(attr,options) {
  			// console.log("PPPPPPPPPPPPPP");
  			// console.log("PPPPPPPPPPPPPP");
  			var self = this;

  			this.order_type = 'retail';
  			posorder_super.initialize.call(this,attr,options);
  		},
  		export_as_JSON: function(){
  			var loaded = posorder_super.export_as_JSON.apply(this, arguments);
  			loaded.order_type = this.order_type || false;
        // this.order_type = 'retail';

  			return loaded;
  		},

  		init_from_JSON: function(json){
  			posorder_super.init_from_JSON.apply(this,arguments);
  			this.order_type = json.order_type;
  		},
  	});


    var TypeButton = screens.ActionButtonWidget.extend({
    	template: 'TypeButton',
      init: function (parent, options) {
          this._super(parent, options);

          this.pos.get('orders').bind('add remove change', function () {
              this.renderElement();
          }, this);

          this.pos.bind('change:selectedOrder', function () {
              this.renderElement();
          }, this);
      },
    	button_click: function(){
        var self = this;
        var list = [];
        list.push({label:"Retail", item:1});
        list.push({label:"Hole Sale", item:2});
        var order = this.pos.get_order();
        self.gui.show_popup('selection',{
          title: 'Order Type',
          list: list,
          confirm: function (id) {
            if(id==1){
              order.order_type = 'retail';
              $(".unfixed_product").css({'display':'none'});
              var prod = self.pos.db.get_product_by_id(562);
              order.add_product(prod);
            }else {
              order.order_type = 'sale';
              $(".unfixed_product").css({'display':'block'});

            }

            // console.log(order);
            order.trigger('change');
          },

        });

    	},
      get_current_type: function () {
          var name = _t('Order Type');
          var order = this.pos.get_order();

          if (order) {
              var order_type = order.order_type;

              if (order_type=='retail') {
                  name = "Retail";
              }else {
                name = 'Hole Sale';
              }
          }
           return name;
      },

    });

    screens.define_action_button({
    	'name': 'orderType',
    	'widget': TypeButton,
    });

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