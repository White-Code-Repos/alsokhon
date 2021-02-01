odoo.define('ks_theme_kinetik.ProductConfiguratorMixin', function (require) {
    'use strict';

    var ProductConfiguratorMixin = require('sale.VariantMixin');;
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.WebsiteSale.include({
        /**
         * Adds the stock checking to the regular _onChangeCombination method
         * @override
         */
        _onChangeCombination: function (){
            this._super.apply(this, arguments);
            var seconds = arguments[2].seconds;
            if(seconds){
             $('.clock').removeClass("d-none");
             var clock = $('.clock').FlipClock(seconds, {
                clockFace: 'DailyCounter',
                            countdown: true,
                });
            }
            else{
                $('.clock').addClass("d-none");
            }

        },
    });

    return ProductConfiguratorMixin;
});