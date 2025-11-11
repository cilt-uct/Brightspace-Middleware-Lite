"use strict";

$(function() {

    $('.vertnav .nav-link:not(dropdown-toggle)').on('click', function(event){
        event.preventDefault();
        const _me = $(this);
        console.log(_me);
        //
        //       _data = getObj(_me.attr('rel'), menu_data);

        // $('.top-nav').html(tmpl('tmpl-top-menu', _data));
        // $('#main-frame').attr('src', _data['load']);
    });

});
