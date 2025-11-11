(function($){

    $.fn.multi_select = function(options) {

        let defaults = {
            reset: false,
            fill: false,
            data: null,
            input: true,
            inputPlaceholder: "Enter ..."
        };

        let settings = $.extend(defaults, options);
        let value = "";

        return this.each(function() {
            $(this).after(`<div class="multi-container"></div>\n` +
                    `<input type="text" name="multi-input" class="form-control multi-input" placeholder=${settings.inputPlaceholder}" />`);

            let $orig = $(this);
            let $element = $(this).siblings('.multi-input');

            if (!settings.input) {
                $element.hide();
            }

            let $container = $(this).siblings('.multi-container');
            let processInput = function() {
                let inp = $element.val().replace(/\s/g, '').split(',').filter(function(s) { return (s != '') && (s); });
                $.each(inp, function(i, st) {
                    $('.multi-container').append('<span class="multi-item" data-val='+ st +'>' + st + '<span class="multi-item-cancel"><i class="fas fa-times"></i></span></span>');
                    $element.val('');
                });
                var dataList = $container.children('.multi-item:not(.wrong)').map(function() {
                    return $(this).data("val");
                }).get();

                $orig.val(dataList.join(',')).trigger('change');
            }
            $element.focusout(function (e) {
                // console.log('focusout');
                processInput();
            });
            $element.keydown(function (e) {
                $element.css('border', '');
                switch(e.keyCode){
                    case 13:
                    case 32:
                        processInput();
                        break;
                    case 27:
                        $element.val('');
                        break;
                }
            });

            $(document).on('click','.multi-item-cancel',function(){
                $(this).parent().remove();

                var dataList = $container.children('.multi-item:not(.wrong)').map(function() {
                    return $(this).data("val");
                }).get();

                $orig.val(dataList.join(',')).trigger('change');
            });

            if(settings.data){
                let inp = settings.data.replace(/\s/g, '').split(',').filter(function(s) { return (s != '') && (s); });
                $.each(inp, function(i, st) {
                    $('.multi-container').append('<span class="multi-item" data-val='+ st +'>' + st + '<span class="multi-item-cancel"><i class="fas fa-times"></i></span></span>');
                    value += st + ','
                })
                $element.val('');
                $orig.val(value.slice(0, -1));
            }

            if(settings.reset){
                $('.multi-item').remove()
            }

            this.initialize = function() {
                $orig.hide();
                return this;
            }

            this.insert = function(str) {
                let inp = str.replace(/\s/g, '').split(',').filter(function(s) { return (s != '') && (s); });

                var dataList = $container.children('.multi-item:not(.wrong)').map(function() {
                    return $(this).data("val");
                }).get() || [];

                $.each(inp, function(i, st) {
                    if (!dataList.includes(st)) {
                        $('.multi-container').append('<span class="multi-item" data-val='+ st +'>' + st + '<span class="multi-item-cancel"><i class="fas fa-times"></i></span></span>');
                        $element.val('');
                        value += st.toLowerCase() + ','
                        dataList.push(st);
                    }
                });

                $orig.val(dataList.join(',')).trigger('change');
            };

            this.setValue = function(str) {
                $container.children().remove(); // reset
                let inp = str.replace(/\s/g, '').split(',').filter(function(s) { return (s != '') && (s); });
                $.each(inp, function(i, st) {
                    $('.multi-container').append('<span class="multi-item" data-val='+ st +'>' + st + '<span class="multi-item-cancel"><i class="fas fa-times"></i></span></span>');
                })
                $element.val('');
                $orig.val(inp.join(',')).trigger('change');
            }

            return this.initialize();
        });
    };

})(jQuery);
