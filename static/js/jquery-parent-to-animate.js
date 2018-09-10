// Usage:
// $('.box').parentToAnimate($('.new-parent'), 200);
// $('.box').parentToAnimate($('.new-parent'), 'slow');
// $('.box').parentToAnimate('.new-parent', 'slow');

jQuery.fn.extend({
    // Modified and Updated by MLM
    // Origin: Davy8 (http://stackoverflow.com/a/5212193/796832)
    parentToAnimate: function(newParent, duration) {
        duration = duration || 'slow';
        
        var $element = $(this);
        
        newParent = $(newParent); // Allow passing in either a JQuery object or selector
        var oldOffset = $element.offset();
        $(this).appendTo(newParent);
        var newOffset = $element.offset();
        
        var temp = $element.clone().appendTo('body');
        
        temp.css({
            'position': 'absolute',
            'left': oldOffset.left,
            'top': oldOffset.top,
            'zIndex': 1000
        });
        
        $element.hide();
            
        temp.animate({
            'top': newOffset.top,
            'left': newOffset.left
        }, duration, function() {
            $element.show();
            temp.remove();
        });
    }
});