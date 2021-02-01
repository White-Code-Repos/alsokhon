odoo.define('pos_lot_select.pos', function(require){
      var screens = require('point_of_sale.screens');
      var core = require('web.core');
      var gui = require('point_of_sale.gui');
      var models = require('point_of_sale.models');
      var PopupWidget = require('point_of_sale.popups');
      var QWeb = core.qweb;
      var chrome = require("point_of_sale.chrome");
      var rpc = require('web.rpc');
      var PosBaseWidget = require('point_of_sale.BaseWidget');

      models.load_fields('product.product',['making_charge_id','making_charge_diamond_id']);
      models.load_fields('product.category',['is_gold','is_scrap','is_diamond','is_assembly']);
      models.load_models({
          model: 'stock.production.lot',
          fields: [],
          // domain: function(self){
          //     // var from = moment(new Date()).subtract(self.config.lot_expire_days,'d').format('YYYY-MM-DD')+" 00:00:00";
          //     if(self.config.allow_pos_lot){
          //         return [];
          //     }
          //     else{
          //         return [['id','=',0]];
          //     }
          // },
          loaded: function(self,list_lot_num){
              self.list_lot_num = list_lot_num;
          },
      });
      models.load_models({
          model: 'gold.purity',
          fields: [],
          loaded: function(self,list_gold_purity){
            // console.log(list_lot_num);
              self.list_gold_purity = {};
          		if(list_gold_purity.length){
          			self.gold_purity = list_gold_purity;
          			for (var i = 0; i < list_gold_purity.length; i++) {
                  self.list_gold_purity[list_gold_purity[i].id] = list_gold_purity[i];
          			}
          		}
              // console.log(self.list_gold_purity);
          },
      });



      // models.Packlotline = models.Packlotline.extend({
      //   export_as_JSON: function(){
      //     console.log("sadasdasdasdfe");
      //       return {
      //           id: this.id,
      //           lot_name: this.get_lot_name(),
      //       };
      //   },
      //
      // });




      var PacklotlineCollection2 = Backbone.Collection.extend({
          model: models.Packlotline,
          initialize: function(models, options) {
              this.order_line = options.order_line;
          },

          get_empty_model: function(){
              return this.findWhere({'lot_name': null});
          },

          remove_empty_model: function(){
              this.remove(this.where({'lot_name': null}));
          },

          get_valid_lots: function(){
              return this.filter(function(model){
                  return model.get('lot_name');
              });
          },


          set_quantity_by_lot: function() {
              if (this.order_line.product.tracking == 'serial' || this.order_line.product.tracking == 'lot') {
                  var valid_lots = this.get_valid_lots();

                  this.order_line.set_quantity(valid_lots.length);
              }
          }
      });

      var OrderlineSuper = models.Orderline;

      models.Orderline = models.Orderline.extend({
          set_product_lot: function(product){
              this.has_product_lot = product.tracking !== 'none' && this.pos.config.use_existing_lots;
              this.pack_lot_lines  = this.has_product_lot && new PacklotlineCollection2(null, {'order_line': this});
          },
          export_for_printing: function(){
              var pack_lot_ids = [];
              if (this.has_product_lot){
                  this.pack_lot_lines.each(_.bind( function(item) {
                      return pack_lot_ids.push(item.export_as_JSON());
                  }, this));
              }
              var data = OrderlineSuper.prototype.export_for_printing.apply(this, arguments);
              data.pack_lot_ids = pack_lot_ids;
              return data;
          },

          get_order_line_lot:function(){
              var pack_lot_ids = [];
              if (this.has_product_lot){
                  this.pack_lot_lines.each(_.bind( function(item) {
                      return pack_lot_ids.push(item.export_as_JSON());
                  }, this));
              }
              return pack_lot_ids;
          },
          get_required_number_of_lots: function(){
              var lots_required = 1;

              if (this.product.tracking == 'serial' || this.product.tracking == 'lot') {
                  lots_required = this.quantity;
              }

              return lots_required;
          },

          has_valid_product_lot: function(){
              if(!this.has_product_lot){
                  return true;
              }
              var valid_product_lot = this.pack_lot_lines.get_valid_lots();
              if (this.pack_lot_lines.models[0]) {
                return this.get_required_number_of_lots() === this.pack_lot_lines.models[0].quantity;
              }
              return false;
              // return this.get_required_number_of_lots() === valid_product_lot.length;
          },


      });

      screens.PaymentScreenWidget.include({

          order_is_valid: function(force_validation) {
              var self = this;

              var order = this.pos.get_order();

              order.orderlines.each(_.bind( function(item) {
                // console.log("item");
                // console.log(item);

                  if(item.pack_lot_lines ){
                    item.pack_lot_lines.each(_.bind(function(lot_item){
                      // console.log(lot_item);

                      var lot_list = self.pos.list_lot_num;
                        for(var i=0;i<lot_list.length;i++){
                            if(lot_list[i].product_id[0]==item.product.id&&lot_list[i].name == lot_item.attributes['lot_name']){
                              console.log(lot_list[i]);
                              // console.log((item.quantity*lot_list[i].gross_weight)/lot_list[i].total_qty);
                              // console.log((item.quantity*lot_list[i].pure_weight)/lot_list[i].total_qty);
                              if (item.product.categ.is_scrap || item.product.categ.is_gold) {
                                // console.log(parseFloat(num.toFixed(3)));
                                // console.log(lot_list[i]);

                                if (lot_list[i].total_qty == 0) {
                                  // console.log(lot_list[i]);
                                  // console.log(lot_list[i].purity_id);
                                  // console.log(self.pos.list_gold_purity[lot_list[i].purity_id[0]]);
                                  var scrap_purity = self.pos.list_gold_purity[lot_list[i].purity_id[0]].scrap_purity/1000;

                                  // console.log(lot_list[i].gross_weight,item.quantity,lot_list[i].total_qty,lot_list[i].gross_weight-item.quantity);
                                  // console.log(lot_list[i].pure_weight,item.quantity,lot_list[i].total_qty,lot_list[i].pure_weight-item.quantity*scrap_purity);
                                  lot_list[i].gross_weight -= item.quantity;
                                  lot_list[i].gross_weight = parseFloat((lot_list[i].gross_weight).toFixed(4))
                                  lot_list[i].pure_weight -= (item.quantity*scrap_purity);
                                  lot_list[i].pure_weight = parseFloat((lot_list[i].pure_weight).toFixed(4))

                                }else {
                                  // console.log(lot_list[i].gross_weight,item.quantity,lot_list[i].total_qty,lot_list[i].gross_weight-(item.quantity*lot_list[i].gross_weight)/lot_list[i].total_qty);
                                  // console.log(lot_list[i].pure_weight,item.quantity,lot_list[i].total_qty,lot_list[i].pure_weight-(item.quantity*lot_list[i].pure_weight)/lot_list[i].total_qty);
                                  lot_list[i].gross_weight -= (item.quantity*lot_list[i].gross_weight)/lot_list[i].total_qty;
                                  lot_list[i].gross_weight = parseFloat((lot_list[i].gross_weight).toFixed(4))
                                  lot_list[i].pure_weight -= (item.quantity*lot_list[i].pure_weight)/lot_list[i].total_qty;
                                  lot_list[i].pure_weight = parseFloat((lot_list[i].pure_weight).toFixed(4))
                                }

                              }else if (item.product.categ.is_diamond&&lot_list[i].total_qty!=1) {
                                lot_list[i].carat -= (item.quantity*lot_list[i].carat)/lot_list[i].total_qty;
                                lot_list[i].carat = parseFloat((lot_list[i].carat).toFixed(4))
                              }

                              // console.log(lot_list[i].total_qty , item.quantity,lot_list[i].total_qty-item.quantity);
                              lot_list[i].total_qty -= item.quantity;
                              lot_list[i].total_qty = parseFloat((lot_list[i].total_qty).toFixed(4))


                            }
                        }
                      },this)
                      );
                    }
                  },this)
                );
                return this._super(force_validation)
            },
        });

      var PackLotLinePopupWidget = PopupWidget.extend({
          template: 'PackLotLinePopupWidget',
          events: _.extend({}, PopupWidget.prototype.events, {
              'click .remove-lot': 'remove_lot',
              'keydown': 'add_lot',
              'blur .packlot-line-input': 'lose_input_focus'
          }),
          get_lots_fields: function () {
      			var fields = [];
      			return fields;
      		},
          get_lots_domain: function(){
            var self = this;
            var from = moment(new Date()).subtract(self.pos.config.lot_expire_days,'d').format('YYYY-MM-DD')+" 00:00:00";
            if(self.pos.config.allow_pos_lot){
                return [['total_qty','>',0]];
            }
            else{
                return [['id','=',0]];
            }
            // return [['product_qty', '>', 0]];
          },
          get_pos_lots: function () {
      			var self = this;
            var product_lot = [];
            var fields = self.get_lots_fields();
            var lot_domain = self.get_lots_domain();
            rpc.query({
                model: 'stock.production.lot',
                method: 'search_read',
                args: [lot_domain,fields],
            }, {async: true}).then(function(output) {
              output.forEach(function(lot) {
                  product_lot.push(lot);
              });
              self.pos.set({'list_lot_num' : product_lot});
              // console.log(product_lot);

            });
      		},




          show: function(options){
              var self = this;
              // self.get_pos_lots();
              var product_lots =  self.pos.list_lot_num;
              var product_lot = []
              // console.log("ptions.order_line");
              // console.log(options.order_line);
              // setTimeout(function(){
              // }, 1000);
              product_lots.forEach(function(lot) {
                // if (lot.product_id[0] == options.pack_lot_lines.order_line.product.id) {
                //   console.log(options.order_line.is_unfixed);
                // }
                  if(lot.product_id[0] == options.pack_lot_lines.order_line.product.id && !options.order_line.is_unfixed && lot.total_qty>0){
                    product_lot.push(lot);
                  }else if (lot.product_id[0] == options.pack_lot_lines.order_line.product.id && options.order_line.is_unfixed) {
                    product_lot.push(lot);
                  }

              });

              // console.log(product_lot);

              // self.render_list_lots(product_lot,undefined);
              options.qstr = "";
              options.add_lot = false;
              // options.is_return = false;
              options.product_lot = product_lot;
              this._super(options);
              // this.focus();
          },
          render_list_lots: function(lots, search_input){
      			var self = this;

      			var content = this.$el[0].querySelector('.lots-list-contents');
      			content.innerHTML = "";
      			var lots = lots;
      			var current_date = null;
      			if(lots){
      				for(var i = 0, len = Math.min(lots.length,1000); i < len; i++){
      					var lot    = lots[i];

      				}
      			}

      		},

          renderElement:function(){
              this._super();
              var self = this;
              $.fn.setCursorToTextEnd = function() {
                  $initialVal = this.val();
                  this.val($initialVal + ' ');
                  this.val($initialVal);
                  };
              $(".search_lot").focus();
              $(".search_lot").setCursorToTextEnd();

              $(".add_lot_number").click(function(){
                var lot_count = $(this).closest("tr").find("input").val();

                // if (self.options.order_line.product.categ.is_gold ) {
                //   var selling_making_charge= $(this).closest("tr").find("#selling_making_charge")[0].innerText;
                // }
                // if (!self.options.order_line.product.categ.is_diamond) {
                //   var pure_weight= $(this).closest("tr").find("#pure_weight")[0].innerText;
                //   var gross_weight= $(this).closest("tr").find("#gross_weight")[0].innerText;
                //   var purity_id= $(this).closest("tr").find("#purity_id")[0].innerText;
                //   var gold_rate= self.pos.config.gold_rate;
                // }

                      var lot = $(this).data("lot");

                      var input_box;

                      $('.packlot-line-input').each(function(index, el){
                              input_box = $(el)
                      });

                      if(input_box != undefined){
                          input_box.val(lot);
                          var pack_lot_lines = self.options.pack_lot_lines,
                              $input = input_box,
                              cid = $input.attr('cid'),
                              lot_name = $input.val();

                          var lot_model = pack_lot_lines.get({cid: cid});

                          lot_model.quantity=parseFloat(lot_count);
                          lot_model.set_lot_name(lot_name);
                          if(!pack_lot_lines.get_empty_model()){
                              var new_lot_model = lot_model.add();
                              self.focus_model = new_lot_model;
                          }

                          pack_lot_lines.order_line.quantity=parseFloat(lot_count);
                          pack_lot_lines.order_line.quantityStr=lot_count;

                          self.renderElement();
                          self.focus();
                      }
                  // }
              });

              $(".search_lot").keyup(function(){
                  self.options.qstr = $(this).val();
                  var lot_list = self.pos.list_lot_num;
                  var product_lot = [];
                  for(var i=0;i<lot_list.length;i++){
                      if(lot_list[i].product_id[0] == self.options.pack_lot_lines.order_line.product.id && lot_list[i].name.toLowerCase().search($(this).val().toLowerCase()) > -1){
                          product_lot.push(lot_list[i]);
                      }
                  }
                  self.options.product_lot = product_lot;
                  self.renderElement();

              });
              $(".new-lot").click(function(){
                if (!self.options.add_lot) {
                  self.options.add_lot=true;
                  $(".new_lot").css({'display':'contents'});
                }else {
                  self.options.add_lot=false;
                  $(".new_lot").css({'display':'none'});
                  var name_lot = $(".name_lot").val();
                  // var gr_wight = $(".gr_wight").val();
                  var puri = $(".puri").val();
                  // var pr_wight = $(".pr_wight").val();
                  // console.log('named',self.check_name(name_lot));
                  // console.log('pure',self.check_purity(puri));

                  puri = self.check_purity(puri);

                  if (self.check_name(name_lot)&&puri) {
                    var list = [{
                      'name': name_lot,
                      'product_qty':0,
                      'gross_weight':0,
                      'pure_weight':0,
                      'total_qty':0,
                      'is_scrap':true,
                      'purity_id':puri.id,
                      'from_pos':puri.id,
                      'product_id':self.options.order_line.product.id,
                      'company_id':self.options.order.pos.company.id
                    }];
                    rpc.query({
                        model: 'stock.production.lot',
                        method: 'create',
                        args: [list],
                    }, {async: true}).then(function(id) {
                      // total_qty
                      // console.log(self.pos.list_lot_num);
                      // console.log(id);
                      list = {
                        'id':id,
                        'name': name_lot,
                        'product_qty':0,
                        'gross_weight':0,
                        'pure_weight':0,
                        'total_qty':0,
                        'from_pos':puri.id,
                        'is_scrap':true,
                        'purity_id':[puri.id,puri.name],
                        'product_id':[self.options.order_line.product.id,self.options.order_line.product.display_name],
                      };
                      // console.log(list);
                      self.pos.list_lot_num.push(list);
                      // output.forEach(function(lot) {
                      //     product_lot.push(lot);
                      // });
                      // self.pos.set({'list_lot_num' : product_lot});
                      // console.log(product_lot);
                      self.show(self.options);

                    });
                  }else {
                    if (!self.check_name(name_lot)) {
                      alert("Name must Be unique");
                    }else {
                      alert("Purity is not exist");
                    }
                  }

                  // self.check_name(name_lot);

                  // console.log(name_lot,puri);
                }
                  console.log("NEEEEEEW");
                  console.log(self.options);
                  // self.gui.show_popup('AddLotWidget');
                  // self.renderElement();
              });
              // $(".is_return_bt").click(function(){
              //
              //     if(self.options.is_return){
              //       $(this)[0].innerText="False";
              //       self.options.is_return=false;
              //     }else {
              //       $(this)[0].innerText="True";
              //       self.options.is_return = true;
              //     }
              //     console.log( self.options);
              //
              //
              //     // self.renderElement();
              // });
          },
          check_name: function(name){
                // console.log(name);
                var self = this;
                var product_lots =  self.options.product_lot;
                var f = true;
                product_lots.forEach(function(lot) {
                  // console.log(lot.name,name,lot.name==name,(lot.name).toLowerCase() == name.toLowerCase());

                    if( (lot.name).toLowerCase() == name.toLowerCase()){
                      f= false;
                      return true;
                    }
                });
                return f;
          },
          check_purity: function(purity){
                // console.log(purity);
                var self = this;
                var f = false;

                // console.log(self.pos.gold_purity);
                var gold_puritys = self.pos.gold_purity;
                gold_puritys.forEach(function(pure) {
                  // console.log(lot.name,name,lot.name==name,(lot.name).toLowerCase() == name.toLowerCase());

                    if( pure.display_name == purity){
                      f= pure;
                      return true;
                    }
                });
                return f;
          },


          change_price: function(gold_rate,pure_weight,qty,tot_qty){
              var pack_lot_lines = this.options.pack_lot_lines;
              // console.log(gold_rate*pure_weight);
              this.options.order_line.price=gold_rate*pure_weight;
          },


          click_confirm: function(){
              self = this
              var pack_lot_lines = this.options.pack_lot_lines;
              this.$('.packlot-line-input').each(function(index, el){
                  var cid = $(el).attr('cid'),
                      lot_name = $(el).val();
                  var pack_line = pack_lot_lines.get({cid: cid});
                  pack_line.set_lot_name(lot_name);

              });

              pack_lot_lines.remove_empty_model();
              // pack_lot_lines.set_quantity_by_lot();
              if(this.options.order_line.pack_lot_lines.models[0]){
                var selected_lot = this.options.order_line.pack_lot_lines.models[0].attributes.lot_name;
                this.options.product_lot.forEach(function(lot) {
                  if (lot.name == selected_lot)
                  {
                    var order_line = self.options.order_line
                    var pure_weight = lot.pure_weight;

                    if (order_line.product.categ.is_scrap) {
                      // console.log(lot);
                      // console.log(self.pos.list_gold_purity[lot.purity_id[0]].scrap_purity);
                      if (!self.pos.list_gold_purity[lot.purity_id[0]].scrap_purity) {
                        pure_weight = 0;
                      }
                      else {
                        pure_weight = self.pos.list_gold_purity[lot.purity_id[0]].scrap_purity/1000;
                      }
                      order_line.purity = self.pos.list_gold_purity[lot.purity_id[0]].name;
                    }

                    // console.log(self.options);
                    if (self.options.order_line.is_unfixed) {
                      self.options.pack_lot_lines.models[0].quantity*=-1;
                      self.options.order_line.quantity*=-1;
                      self.options.order_line.quantityStr=String(self.options.order_line.quantity);
                    }
                    // console.log(pure_weight);



                    if (order_line.product.categ.is_scrap||order_line.product.categ.is_gold) {
                      self.change_price(self.pos.config.gold_rate,pure_weight);
                    }

                    if(order_line.product.categ.is_gold && order_line.product.making_charge_id ){
                      var product = self.pos.db.get_product_by_id(self.options.order_line.product.making_charge_id[0]);
                      self.options.order.add_product(product, {
                        quantity: 1,
                        price: order_line.quantity * lot.gross_weight * lot.selling_making_charge,
                      });
                    }
                    if(order_line.product.categ.is_diamond && order_line.product.making_charge_diamond_id ){
                      var product = self.pos.db.get_product_by_id(self.options.order_line.product.making_charge_diamond_id[0]);
                      self.options.order.add_product(product, {
                        quantity: 1,
                        price: order_line.quantity * lot.selling_making_charge,
                      });
                    }
                  }
                  // order_ids.push(order.id)
                  // self.pos.db.get_orders_by_id[order.id] = order;
                });
              }

              // var selling_making_charge= $(this).closest("tr").find("#selling_making_charge")[0].innerText;
              // var pure_weight= $(this).closest("tr").find("#pure_weight")[0].innerText;
              // var gross_weight= $(this).closest("tr").find("#gross_weight")[0].innerText;
              // var purity_id= $(this).closest("tr").find("#purity_id")[0].innerText;
              // var gold_rate= $(this).closest("tr").find("#gold_rate")[0].innerText;
              //
              // self.change_price(gold_rate,pure_weight);
              console.log(this.options.order_line);


              // this.options.order_line.price=0;

              this.options.order.save_to_db();
              this.options.order_line.trigger('change', this.options.order_line);
              this.gui.close_popup();
          },

          add_lot: function(ev) {
              if (ev.keyCode === $.ui.keyCode.ENTER && this.options.order_line.product.tracking == 'serial'){
                  var pack_lot_lines = this.options.pack_lot_lines,
                      $input = $(ev.target),
                      cid = $input.attr('cid'),
                      lot_name = $input.val();
                  //     console.log("((pack_lot_lines))");
                  // console.log(pack_lot_lines);

                  var lot_model = pack_lot_lines.get({cid: cid});
                  lot_model.set_lot_name(lot_name);  // First set current model then add new one
                  if(!pack_lot_lines.get_empty_model()){
                      var new_lot_model = lot_model.add();
                      this.focus_model = new_lot_model;
                  }
                  // pack_lot_lines.set_quantity_by_lot();
                  this.renderElement();
                  this.focus();
              }
          },

          remove_lot: function(ev){
              var pack_lot_lines = this.options.pack_lot_lines,
                  $input = $(ev.target).prev(),
                  cid = $input.attr('cid');
              var lot_model = pack_lot_lines.get({cid: cid});
              lot_model.remove();
              pack_lot_lines.order_line.set_quantity(0)
              // pack_lot_lines.set_quantity_by_lot();
              this.renderElement();
          },

          lose_input_focus: function(ev){
              var $input = $(ev.target),
                  cid = $input.attr('cid');
              var lot_model = this.options.pack_lot_lines.get({cid: cid});
              lot_model.set_lot_name($input.val());
          },

          focus: function(){
              this.$("input[autofocus]").focus();
              this.focus_model = false;   // after focus clear focus_model on widget
          }
      });

      var GoldRateWidget = PosBaseWidget.extend({
          template: 'GoldRateWidget',
          init: function(parent, options){
              options = options || {};
              this._super(parent,options);
          },
          get_rate: function(){
              var rate = parseFloat((this.pos.config.gold_rate).toFixed(4));
              this.pos.config.gold_rate =  parseFloat((this.pos.config.gold_rate).toFixed(4));

              console.log("rate");
              console.log(rate);
              // console.log(this.pos.config);
              return rate;
              // if(rate){
              //     return rate;
              // }else{
              //     return "";
              // }
          },
      });

      chrome.Chrome.include({
          build_widgets: function(){
              this.widgets.push({
                'name':   'goldrate',
                'widget': GoldRateWidget,
                'replace':  '.placeholder-GoldRateWidget',
                });
              this._super();
          },
      });

      gui.define_popup({name:'packlotline', widget:PackLotLinePopupWidget});

      return {
          GoldRateWidget:GoldRateWidget,
      };
    });
