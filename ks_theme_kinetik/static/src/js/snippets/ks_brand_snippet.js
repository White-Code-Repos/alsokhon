odoo.define('website_snippet_brands', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');

    sAnimation.registry.snippet_featured_home_page = sAnimation.Class.extend({
        selector: ".ks_brands_home_page",
        //Get all the records iterate through all records
        disabledInEditableMode: false,
        handleRecords:function(data){
              var aos_delay  = 0;
              _.each(data,function(e){
                    aos_delay = aos_delay+50;
                    this._handleRecord(e,aos_delay);
              },this);
        },

       //Create a section for each record and append it to main snippet
        _handleRecord:function(record,aos_delay){
               var $parent_div = $("<div data-aos='fade-left' data-aos-duration='500' data-aos-easing='ease-in-out' data-aos-delay="+ aos_delay+" data-aos-once='true' class='col_2 p-2 mt-lg-5 mt-2'>")
               //Sending brand in the filter so default search filter cab used for the process
               var ks_model =  "ks_product_manager.ks_brand";
               var $per_off;
               var $a = $("<a href='/shop?filter=brand_"+record.brand_name+"'"+" class='text-center'>");

               var $inner_div = $("<div class='flex-column justify-content-center'>");
               var $img_outer_div = $("<div class='brand__img rounded-circle m-auto'>");
               var $logoUri = "/web/image/"+ks_model+"/" + record.brand_id + "/ks_brand_logo";
               var $brand_log_div = $("<div class='brand__logo position-relative bg-white flex-center m-auto'>");
               var $logo_img = $("<img src="+$logoUri+" class='w-100'/>");
               var $img = $('<img>');
               if (record.brand_discount >= 0) {
                 $per_off = $("<div class='brand__offer mt-2 text-center'>Min "+record.brand_discount+"% OFF</div>");
               }
               else{
                    $per_off = $("<div></div>");
               }
               var $imgUri = "/web/image/"+ks_model+"/" + record.brand_id + "/ks_image";
               $img.attr('data-lazy', $imgUri);
               $img.attr('src', $imgUri);
               $img_outer_div.append($img);
               $inner_div.append($img_outer_div);
               $a.append($inner_div);
               $parent_div.append($a);
               $brand_log_div.append($logo_img)
               $parent_div.append($brand_log_div);
//               $parent_div.append($per_off);
               this.$el.append($parent_div);
               $('.snippet_brands_home_page').removeClass('d-none');
        },

        //fix me
        //Find alternate of the html("")
        start: function () {
            var self = this;
            self.getRecords();
            $(".ks_brands_home_page").html("");
            return this._super();

        },
         getRecords: function() {
            var ks_self = this;
            //Fetching all the brands and rendering it with in snippet
            ajax.jsonRpc("/product_brands", 'call', {}).then(function (data) {
                    ks_self.handleRecords(data);
            });
        },
    });

});


