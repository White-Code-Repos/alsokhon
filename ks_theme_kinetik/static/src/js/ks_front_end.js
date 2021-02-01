$(document).ready(function(){

     $('.ks-loader-outer').fadeOut();

      function mobileToggleView(){
            $('.search_container:not(.search-container-7) .mobile-toggle-button #search-btn').click(function(ev){
                $(".search-query").val("");
                if($('.search_container:not(.search-container-7)').hasClass('search__in')){
                    $('.search_container:not(.search-container-7)').removeClass('search__in');
                } else {
                    $('.search_container:not(.search-container-7)').addClass('search__in');
                }

                if($(this).hasClass('fa-search')) {
                    $(this).removeClass('fa-search');
                    $(this).addClass('fa-times');
                }
                else {
                    $(this).removeClass('fa-times');
                    $(this).addClass('fa-search');
                }
          });
       }
       mobileToggleView();


         if($(document).width() < 767) {
            // This is used to remove class for product detail page  vertical multi image responsiveness fix
             if($('#ks_verti_img').hasClass('ks_test_vertical')){
                  $('#ks_verti_img').removeClass('ks_test_vertical');
             }
         };



        if ($('.o_wsale_layout_list').length){
            $('.o_wsale_layout_list').find('.o_wsale_products_grid_table_wrapper').addClass('ks_products_table ks-product-list-view m-auto');
        }
        else{
          $('#products_grid').addClass('ks_products_table');
        }
        $(document).on('hide.bs.modal',$('.o_select_options').parents('.modal').attr('id'), function(ev){
               $('#product_details').removeClass('ks_cart_on_product_detail');
                });
        if(parseInt($('.page_count').val())===1){
                 $('.product_load_more').addClass('d-none');
        }


        $(".ks-scroll-top").click(function() {
          $("html, body").animate({ scrollTop: 0 },1200);
        });


        //open filter
        //Hide default pagination if products getting load using ajax
        $('.ks_filter_button').click(function(){
            $('#products_grid_before').addClass('ks-show-filter');
             if($(".is_ks_load_ajax").length > 0){
                $('.ks-price-filter-apply').addClass('d-none')
             }
             else{
                $('.ks-price-filter-apply').removeClass('d-none')
               _.each($(".products_pager .pagination"),function(pager){
                    $(pager).removeClass("d-none");
                });
             }
             $('#products_grid_before').removeClass('ks-hide-filter');
            $('.ks-filter-overlay').addClass('d-block');
            $('body').addClass('js-no-scroll');
        });

        //close filter
         $('.ks-filter-overlay').on('click', function(e) {
            $('#products_grid_before').addClass('ks-hide-filter');
            $('.ks-filter-overlay').delay(500).queue(function() {
                $('#products_grid_before').removeClass('ks-show-filter');
                 $('.ks-filter-overlay').removeClass('d-block');
                 $('body').removeClass('js-no-scroll');
                 $('.ks-filter-overlay').dequeue();
             });

        });

    //search for header 6
	$('.ks-search-trigger').click(function(){
	    $('.ks-header-6-search').toggleClass('js-search-show');
	    $(this).toggleClass('js-search-hide');
	});

    $('.js_usermenu').parent().addClass('ks_landing_menu');

    if($('.ks-filter-outer .nav-link input[type="checkbox"]').prop("checked") == true) {
        $('.ks-filter-outer .nav-link input[checked="checked"]').parents("ul.collapse").prev().trigger( "click" ); ;
    }



        //correcting z-index on header 7's input click
         $('.search-container-7 input').focusin(function() {
                $('#wrapwrap').addClass('js-change-indexes-h7');
         });

        $('.search-container-7 input').focusout(function() {
                $('#wrapwrap').removeClass('js-change-indexes-h7');
         });
         if ($('.o_wsale_my_cart').find('sup').text()==''){
         $('.o_wsale_my_cart').find('sup').text('0');
         $('.o_wsale_my_cart').removeClass('d-none');
         }
         //correcting z-index on header 8's input click
         $('.ks-header-8-topmost .nav__search_icon').click(function() {
                $('#wrapwrap').toggleClass('js-change-indexes-h8');
         });
        //Handling category mega menu after scrolling
        $(document).on('mouseenter','.ks_vertical_tabs .nav-tabs .nav-link',function(){
            $(this).trigger('click');
            var a = this.href.split("#")[1]
            $('.ks_cat_menu').removeClass('active')
            $('.'+a).addClass('active')
        });
        // Handling multiple multitab active
        $(document).on('click','#new_arrivals',function(ev){
            var a=ev.currentTarget.parentElement.href.split('#')[1]
            var slider_id=$('.'+a+'slider_id').val()
            $('.ks_multitab-'+slider_id).removeClass('active')
            $('.'+a).addClass('active ')
            $('.ks_tab_list'+slider_id).find('a').removeClass('active')
            $('.'+a+'slider_id').siblings().addClass('active');
        })

    // ***** triggering animation when in Screen viewport ***** \\
        $('.animated').addClass('no-animation');
         function inViewport(){
             $('.no-animation').each(function(){
                 var divPos = $(this).offset().top,
                     topOfWindow = $(window).scrollTop();

                 if( divPos < topOfWindow + 600 ){
                     $(this).removeClass('no-animation');
                 }
             });
         }

         $(window).scroll(function(){
             inViewport();
         });
         $(window).on("resize", function (e) {
            inViewport();
             if($(window).width() < 1280){
                $('body').removeClass('toggle-navigation');
                $('body > #wrapwrap').removeClass('js-menu-opened');
                $('body').removeClass('js-menu-opened');
                $('.navbar-collapse').removeClass('show');
             }
         });


         //for stopping extra menus click
        $(document).on("show.bs.dropdown","li.o_extra_menu_items",function(ev){
             return false;
         });

         function mobileToggle(){
            $(document).on('click','.o_affix_enabled button.navbar-toggler',function(){
               if ($('body > #wrapwrap').hasClass('js-menu-opened')) {
                   $('body > #wrapwrap').removeClass('js-menu-opened');
                   $('body').removeClass('toggle-navigation');
               }
               else{
                    $('body > #wrapwrap').addClass('js-menu-opened');
                    $('body').addClass('toggle-navigation');
                }
            });
            $(document).on('click','.o_header_affix .navbar-toggler',function(){
              $('body').toggleClass('js-menu-opened');
           });
         }
        //for stopping scroll while navbar menu is opened
        mobileToggle();

        var filter_len = $('.ks-filter-outer').length;
        if(!filter_len){
            $('.ks_product_categories_before').removeClass("ks-only-categories").addClass("ks-only-categories");
        }

       var is_custom_sign_up = $(".ks-custom-login").length;
       if(is_custom_sign_up){
           $('.ks-default-login').addClass('d-none')
        }

        if($(window).width() < 990){
          $('.navbar-expand-md').addClass('navbar-expand-lg ks-default-header');
          $('.ks-default-header').removeClass('navbar-expand-md');

         }

         $('.h3').parent().addClass('ks_suggested_products');
         if ($('.ks_suggested_products').find('a').length==0){
         $('.ks_suggested_products').addClass('d-none')
         }

         _.each($('.ks_menu_heading'),function(ev){
            if ($(ev).text()==' '){
            $(ev).removeClass('d-block')
            $(ev).addClass('d-none')
            }
         })

         $(document).on('click','.navbar-toggler',function(ev){
            $('.ks-header-offer').toggleClass('ks_header_menu_toggled');
         });

         //Footer fix for shop page only
         $('#product_detail').parents("main").next().addClass("ks_shop_page_footer");

         new WOW().init();
});