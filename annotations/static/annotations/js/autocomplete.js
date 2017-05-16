var bindAutocomplete = function(selector, pos) {

    $(function() {
        function split( val ) {
            return val.split( /,\s*/ );
        }
        function extractLast( term ) {
            return split( term ).pop();
        }

        $(selector)
            // don't navigate away from the field on tab when selecting an item
            .bind( "keydown", function( event ) {
                if ( event.keyCode === $.ui.keyCode.TAB &&
                    $( this ).autocomplete( "instance" ).menu.active ) {
                        event.preventDefault();
                    }
            })
            .autocomplete({
                source: function( request, response ) {
                    $(this).addClass('ajax-loading');
                    $.getJSON(BASE_URL + "/rest/concept/search", {
                        search: extractLast( request.term ),
                        pos: pos,
                        remote: true,
                    }, function(data){
                        $(this).removeClass('ajax-loading');
                        response(data.results);
                    } );
                },
                search: function() {
                    // custom minLength
                    var term = extractLast(this.value);
                    if ( term.length < 3 ) {
                        return false;
                    }
                },
                focus: function() {
                    return false;
                },
                select: function( event, ui ) {
                    this.value = ui.item.value;
                    $(this).attr('concept_id', ui.item.uri);
                    var target = $(this).attr('target');
                    var description_target = $(this).attr('description');
                    if (target) {
                        $('#' + target).val(ui.item.uri);
                    }
                    if (description_target) {
                        $('#' + description_target).text(ui.item.description);
                        $('#' + description_target).css("visibility", "visible");
                    }
                    return false;
                }
            })
            .autocomplete( "instance" )._renderItem = function( ul, item ) {
                ul.addClass('list-group');
                return $( "<a class='list-group-item' style='cursor: pointer;'>" )
                    .append( "" + item.label + "<br><span class='text-muted'>" + item.description + "</span>" )
                    .appendTo( ul );
            };
        });
}
