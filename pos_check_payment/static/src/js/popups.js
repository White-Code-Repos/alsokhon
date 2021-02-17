odoo.define('pos_check_payment.popups', function (require) {
"use strict";

var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');

var CheckInfoWidget = PopupWidget.extend({
    template: 'CheckInfoWidget',
    show: function(options){
        options = options || {};
        this._super(options);
        this.renderElement();
        this.$('.popup-checkinfo .detail')[0].focus()
    },
    get_infos: function() {
      console.log(this.options);
        return {
            'check_bank_id' : parseInt(this.$('select[name=check_bank_id]').val()) || undefined,
            'check_number'  : this.$('input[name=check_number]').val(),
            // 'check_owner'   : this.options.data.client.id,
            'check_owner'   : this.$('input[name=check_owner]').val(),
            'check_issue_date'   : this.$('input[name=check_issue_date]').val(),
            'check_payment_date'   : this.$('input[name=check_payment_date]').val(),
        };
    },
    click_confirm: function(){
      console.log("WQRWQEQWDSDASDASDASDAS");
      console.log(this.get_infos());

        var infos = this.get_infos();
        var valid = true;
        console.log(this.options);
        if(this.options.validate_info){
            valid = this.options.validate_info.call(this, infos);
        }

        if(!valid) return;

        this.gui.close_popup();
        if( this.options.confirm ){
            this.options.confirm.call(this, infos);
        }
    },
});
gui.define_popup({name:'check-info-input', widget: CheckInfoWidget});


return {
    PopupWidget: PopupWidget,
    CheckInfoWidget: CheckInfoWidget,
};
});
