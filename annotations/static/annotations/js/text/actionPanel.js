// If the window scrolls below the top of the main content, the right-
//  hand column should scroll with it.
function sticky_relocate() {
    var window_top = $(window).scrollTop(),
        window_width = $(window).width(),
        window_height = $(window).height(),
        div_top = $('#main-container').offset().top;


    // If the window is narrow, the action panel is overlayed on the
    //  text at the bottom of the window.
    if (window_width < 768) {   // Bootstrap sm/xs breakpoint is 768px.
        $('#sticky').removeClass('fixed');
        $('#sticky').addClass('fixed-bottom');
        $('#sticky').addClass('col-xs-12');

        // The action panel should scale vertically with window height.
        $('.action-body').css('max-height', screen.height / 5);

    // If the window is wide enough, the action panel stays on the far
    //  right, and sticks to the top of the window as the user scrolls.
    } else {
        $('.action-body').css('max-height', screen.height/3);
        $('#sticky').removeClass('fixed-bottom');
        $('#sticky').removeClass('col-xs-12');
        if (window_top > div_top) {
            $('#sticky').addClass('fixed');
            // Setting position: fixed removes the element from the
            //  flow, so this applies the appropriate left-offset.
            $('#sticky').addClass('col-sm-offset-8');
        } else {
            // The user hasn't scrolled below the navbar, so we keep
            //  the action panel in the grid.
            $('#sticky').removeClass('fixed');
            $('#sticky').removeClass('col-sm-offset-8');
        }
    }
}

$(function() {
    $(window).scroll(sticky_relocate);
    $(window).resize(sticky_relocate);
    sticky_relocate();
});
