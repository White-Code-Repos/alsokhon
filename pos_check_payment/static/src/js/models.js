odoo.define('pos_check_payment.models', function (require) {
"use strict";

var models = require('point_of_sale.models');

//load new field 'check_info_required', etc
models.load_fields('pos.payment.method','is_check');
// models.load_fields("account.journal", ['check_info_required', 'check_auto_fill_amount', 'check_bank_name_visible',
// 'check_bank_name_required', 'check_bank_acc_visible', 'check_bank_acc_required', 'check_owner_visible', 'check_owner_required']);

//load model res.bank
models.load_models({
    model: 'res.bank',
    fields: ['name'],
    loaded: function(self, banks){
        self.banks = banks;
    },
}, {after: 'res.country'});

var paymentline_super = models.Paymentline.prototype;
models.Paymentline = models.Paymentline.extend({
    init_from_JSON: function (json) {
        paymentline_super.init_from_JSON.apply(this, arguments);

        this.check_bank_id = json.check_bank_id;
        // this.check_bank_acc = json.check_bank_acc;
        this.check_number = json.check_number;
        this.check_owner = json.check_owner;
        this.check_issue_date = json.check_issue_date;
        this.check_payment_date = json.check_payment_date;
    },
    export_as_JSON: function () {
        return _.extend(paymentline_super.export_as_JSON.apply(this, arguments), {
            check_bank_id: this.check_bank_id,
            // check_bank_acc: this.check_bank_acc,
            check_number: this.check_number,
            check_owner: this.check_owner,
            check_issue_date : this.check_issue_date,
            check_payment_date : this.check_payment_date
        });
    },
});

var order_super = models.Order.prototype;
models.Order = models.Order.extend({
    add_paymentline_with_check: function(payment_method, infos) {
        this.assert_editable();
        var newPaymentline = new models.Paymentline({},{order: this, payment_method:payment_method, pos: this.pos});
        $.extend(newPaymentline, infos);
        if(!payment_method.is_cash_count || this.pos.config.iface_precompute_cash){
            newPaymentline.set_amount( this.get_due() );
        }
        this.paymentlines.add(newPaymentline);
        this.select_paymentline(newPaymentline);
        console.log("UWUIOUQOQ");
    },

    update_paymentline_with_check: function(paymentline, infos) {
        this.assert_editable();
        $.extend(paymentline, infos);
        this.select_paymentline(paymentline);
    },
});

return models;
});
