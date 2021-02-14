odoo.define('pos_orders_notes.pos_orders_notes', function (require) {
"use strict";
    var module = require('point_of_sale.models');
    var core = require('web.core');
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var PosPopWidget = require('point_of_sale.popups');
    var models = require('point_of_sale.models');
    var QWeb = core.qweb;
    var _t = core._t;

    models.load_fields('product.product',['shortcut_note']);
    module.load_models({
        model: 'order.note',
        fields: ['id','name'],
        loaded: function(self,order_note){
            self.order_note = order_note;
        },
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            _super_orderline.initialize.call(this,attr,options);
            this.extra_note = this.extra_note || "";
        },
        set_extra_note: function(extra_note){
            this.extra_note = extra_note;
            this.trigger('change',this);
        },
        get_extra_note: function(){
            return this.extra_note;
        },
        export_as_JSON: function(){
            var json = _super_orderline.export_as_JSON.call(this);
            json.extra_note = this.extra_note;
            return json;
        },
        init_from_JSON: function(json){
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.extra_note = json.extra_note;
        },
        export_for_printing: function(){
            var data = _super_orderline.export_for_printing.apply(this, arguments);
            data.extra_note = this.extra_note || "";
            return data;
        }
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attr, options) {
            _super_order.initialize.call(this,attr,options);
            this.note = this.note || "";
        },
        set_extra_note: function(note){
            this.note = note;
            // this.trigger('change',this);
        },
        get_extra_note: function(){
            return this.note;
        },
        export_as_JSON: function(){
            var json = _super_order.export_as_JSON.call(this);
            json.note = this.note;
            return json;
        },
        init_from_JSON: function(json){
            _super_order.init_from_JSON.apply(this,arguments);
            this.note = json.note;
        },
        export_for_printing: function(){
            var data = _super_order.export_for_printing.apply(this, arguments);
            data.note = this.note;
            return data;
        }
    });

    var OrderlineNoteExButton = screens.ActionButtonWidget.extend({
        template: 'OrderlineNoteExButton',
        button_click: function(){
            var line = this.pos.get_order().get_selected_orderline();
            var resto_shortcut_note = [];
            var resto_shortcut_note2 = [];
            if(line){
                var note_ids = line.product.shortcut_note;
                resto_shortcut_note = note_ids;
                resto_shortcut_note2 = this.pos.config.shortcut_note;
                var shortcut_list = []
                var resto_order_note = this.pos.order_note;
                for(var i=0;i<resto_order_note.length;i++){
                    if(resto_shortcut_note.indexOf(resto_order_note[i].id)>-1 || resto_shortcut_note2.indexOf(resto_order_note[i].id)>-1){
                        shortcut_list.push(resto_order_note[i]);
                    }
                }
                this.gui.show_popup('pos-ext-note-popup',{'note':line.get_extra_note(),'is_order_line':true,'shortcut_list':shortcut_list});
            }
        },
    });

    screens.define_action_button({
        'name': 'order_ex_line_note',
        'widget': OrderlineNoteExButton,
        'condition': function(){
            return this.pos.config.allow_line_note;
        },
    });
    var OrderNoteExButton = screens.ActionButtonWidget.extend({
        template: 'OrderNoteExButton',
        button_click: function(){
            var self = this;
            var order = self.pos.get_order();
            var shortcut_list = []
            var resto_shortcut_note = this.pos.config.shortcut_note;
            var resto_order_note = this.pos.order_note;
            for(var i=0;i<resto_order_note.length;i++){
                if(resto_shortcut_note.indexOf(resto_order_note[i].id)>-1){
                    shortcut_list.push(resto_order_note[i]);
                }
            }
            if(order){
                self.gui.show_popup('pos-ext-note-popup',{'note':order.get_extra_note(),'is_order_line':false,'shortcut_list':shortcut_list});
            }
        },
    });

    screens.define_action_button({
        'name': 'order_ex_note',
        'widget': OrderNoteExButton,
        'condition': function(){
            return this.pos.config.allow_order_note;
        },
    });
    // screens.PaymentScreenWidget.include({
    //     renderElement: function() {
    //         var self = this;
    //         this._super();
    //         this.$('.order_note_button').click(function(){
    //             var order = self.pos.get_order();
    //             if(order){
    //                 self.gui.show_popup('pos-ext-note-popup',{'note':order.get_extra_note(),'is_order_line':false});
    //             }
    //         });
    //     },
    // });

    var PosExtNotePopupWidget = PosPopWidget.extend({
    template: 'PosExtNotePopupWidget',
        renderElement: function(){
            this._super();
            var self = this;
            $(".save_order_line_note").click(function(){
                var order = self.pos.get('selectedOrder');
                order.selected_orderline.set_extra_note($(".order_line_note").val());
                self.gui.show_screen('products');
            });
            $(".save_order_note").click(function(){
                var order = self.pos.get('selectedOrder');
                order.set_extra_note($(".order_line_note").val());
                self.gui.show_screen(self.gui.get_current_screen());
            });
            $(".shortcut_button").click(function(){
                var cvalue = $(this).html();
                var current_val = $(".order_line_note").val();
                $(".order_line_note").val(current_val+" "+cvalue+",");
            });
        },
        show: function(options){
            var self = this;
            this.options = options || {};
            this.options.order_note = self.pos.order_note;
            this._super(options);
            this.renderElement();
        },
    });

    gui.define_popup({
        'name': 'pos-ext-note-popup',
        'widget': PosExtNotePopupWidget,
    });
});
