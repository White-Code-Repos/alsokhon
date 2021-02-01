odoo.define('website_deal_of_the_day', function(require) {
    "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    var ks_interval;

    sAnimation.registry.snippet_offer_timer = sAnimation.Class.extend({
       selector: ".ks_offer_timer_class",
       disabledInEditableMode: false,
       template: 'ks_dynamic_offer_snippets',
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_offer_timer.xml'],
       ks_handleTimerRecords:function(data){
          var $inner_temp = $(QWeb.render('ks_dynamic_offer_snippets', {
                "Data":data,
               }));
          $inner_temp.appendTo(this.$el);
       },
       start: function () {
            var self = this;
            self.ks_getTimerOfferRecords();
            this.$el.empty();
            $(".ks_offer_timer_class").html();
            return this._super();
        },
        ks_getTimerOfferRecords:function(data){
            var ks_self = this;
            var tags = {}
            ajax.jsonRpc("/ks_deal_of_the_day", 'call', {}).then(function (data) {
                var seconds;
                var url;
                seconds = data[0];
                url = data[1];
                if(seconds > 0){
                    ks_self.ks_handleTimerRecords(data);

                }
                if(seconds > 0){
                 if ($('.clock_offer').length){
                        var clock_offer = $('.clock_offer').FlipClock(seconds, {
                        clockFace: 'DailyCounter',
                        countdown: true,
		         });}
		         }
		         if(seconds=0) $('#ks_deals_of_the_day').addClass('d-none');
//		         $('.ks_deal').on('click',function(e){
//                    alert();
//         });
             });
          },
    });
});



