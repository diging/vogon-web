var evaluateNodeType = function(elem) {
    var id = elem.attr('id'),
        part = elem.attr('part'),
        name = elem.attr('name'),
        value = elem.val();



    var prefix_parts = name.split('-');
    var prefix = prefix_parts.slice(0, prefix_parts.length - 1).join('-');


    if (value == 'TP') {
        $('#' + prefix + '-' + part + '_type_container').css('display', 'block');
        $('#' + prefix + '-' + part + '_concept_text_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_relationtemplate_internal_id_container').css('display', 'none');
    } else if (value == 'CO') {
        $('#' + prefix + '-' + part + '_type_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_concept_text_container').css('display', 'block');
        $('#id_' + prefix + '-' + part + '_concept_results_elem').css('display', 'block');
        // $('#' + prefix + '-' + part + '_concept_text_container').css('display', 'block');
        $('#' + prefix + '-' + part + '_relationtemplate_internal_id_container').css('display', 'none');
    } else if (value == 'RE') {
        $('#' + prefix + '-' + part + '_type_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_concept_text_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_relationtemplate_internal_id_container').css('display', 'block');

        $('#' + prefix + '-' + part + '_description_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_label_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_prompt_text_container').css('display', 'none');
    } else {
        $('#' + prefix + '-' + part + '_type_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_concept_text_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_relationtemplate_internal_id_container').css('display', 'none');

        $('#' + prefix + '-' + part + '_description_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_label_container').css('display', 'none');
        $('#' + prefix + '-' + part + '_prompt_text_container').css('display', 'none');
    }

    if (value == 'TP' | value == 'CO' | value == 'DT') {
        $('#' + prefix + '-' + part + '_description_container').css('display', 'block');
        $('#' + prefix + '-' + part + '_label_container').css('display', 'block');
        $('#' + prefix + '-' + part + '_prompt_text_container').css('display', 'block');
    }
}


var cloneMore = function(selector, type) {
    var newElement = $(selector).clone(false);
    var total = Number($('#id_parts-TOTAL_FORMS').val());

    newElement.find('div').each(function() {
        var attrs = {};
        if ($(this).attr('id')) {
             attrs['id'] = $(this).attr('id').replace('-' + (total-1) + '-','-' + total + '-');
             attrs['selected-object'] = 'searchStr_' + total;
        }
        if ($(this).attr('name')) {
             attrs['name'] = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
        }

        $(this).attr(attrs);
    });

    newElement.find(':input').each(function() {
        var attrs = {};
        var elem = $(this);
        if ($(this).attr('ng-model')) {
            attrs['ng-model'] = $(this).attr('ng-model').replace('_' + (total-1) + '_','_' + total + '_');
        }

        Array('id', 'description', 'name', 'target', 'results-target', 'status-target').forEach(function(name) {
            if (elem.attr(name)) {
                attrs[name] = elem.attr(name).replace('-' + (total-1) + '-','-' + total + '-');
            }
        })

        if ($(this).attr('type') == 'checkbox') {   // For prompt-text fields.
            $(this).prop('checked', true);

        }

        if ($(this).attr('concept_id')) {   // For specific concept fields.
            attrs['concept_id'] = '';
        }

        $(this).attr(attrs);

        // Increment internal_id, but avoid messing with the relation_internal_id fields.
        if ($(this).attr('name').indexOf('internal_id') > -1 & $(this).attr('name').indexOf('relation') == -1) {
            $(this).val(total);
        } else {
            // This might be overkill....
            $(this).val('');
            $(this).removeAttr('value');
            $(this).removeProp('value');
        }
    });

    newElement.find('li').each(function() {
        var attrs = {};
        if ($(this).attr('id')) {
            attrs['id'] = $(this).attr('id').split('-' + (total-1) + '-').join('-' + total + '-');
        }
        $(this).attr(attrs);

    })
    newElement.find('label').each(function() {
        if ($(this).attr('for')) {
            var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
            $(this).attr('for', newFor);
        }
    });
    newElement.find('#form_ident').each(function() {
        $(this).text(total);
    });

    total++;
    $('#id_parts-TOTAL_FORMS').val(total);

    $('#add_form_row').before(newElement);
    // $scope.relation_options.push(total - 1);

}

var bindTypeField = function() {
    $('.node_type_field').each(function(i, elem) {
        evaluateNodeType($(elem));
    });
    $('.node_type_field').on('change', function() {
        evaluateNodeType($(this));
    });
}

var bindAutocomplete = function(input_elem, pos) {
    var results_elem = $('#' + input_elem.attr('results-target'));
    var status_elem = $('#' + input_elem.attr('status-target'));
    var target = $('#' + input_elem.attr('target'));

    status_elem.removeClass('glyphicon-time');
    status_elem.removeClass('glyphicon-exclamation-sign');
    status_elem.removeClass('glyphicon-ok');
    status_elem.removeClass('glyphicon-hourglass');
    status_elem.addClass('glyphicon-search');
    input_elem.keyup(function() {
        var q = input_elem.val();
        if (searchPromise != null) {
            results_elem.empty();
            clearTimeout(searchPromise);
        }
        status_elem.removeClass('glyphicon-search');
        status_elem.removeClass('glyphicon-exclamation-sign');
        status_elem.removeClass('glyphicon-hourglass');
        status_elem.removeClass('glyphicon-ok');
        status_elem.addClass('glyphicon-time');

        searchPromise = setTimeout(function() {
            status_elem.removeClass('glyphicon-time');
            status_elem.removeClass('glyphicon-search');
            status_elem.removeClass('glyphicon-exclamation-sign');
            status_elem.removeClass('glyphicon-ok');
            status_elem.addClass('glyphicon-hourglass');
            $.get(BASE_URL + "/rest/concept/search", {
                    search: q,
                    pos: pos,
                    remote: true,
                })
                .done(function(response) {
                    status_elem.removeClass('glyphicon-time');
                    status_elem.removeClass('glyphicon-exclamation-sign');
                    status_elem.removeClass('glyphicon-ok');
                    status_elem.removeClass('glyphicon-hourglass');
                    status_elem.addClass('glyphicon-search');
                    response.results.forEach(function(result) {
                        $("<a class='list-group-item' style='cursor: pointer;'>")
                            .click(function() {
                                target.val(result.uri);
                                input_elem.val(result.label);
                                results_elem.empty();
                                searchPromise = null;
                                status_elem.removeClass('glyphicon-time');
                                status_elem.removeClass('glyphicon-search');
                                status_elem.removeClass('glyphicon-hourglass');
                                status_elem.removeClass('glyphicon-exclamation-sign');
                                status_elem.addClass('glyphicon-ok');
                            })
                            .append("" + result.label + "<br><span class='text-muted'>" + result.description + "</span>" )
                            .appendTo(results_elem);
                    });
                })
                .fail(function(xhr, status, error) {
                    console.log(xhr, status, error);
                    status_elem.removeClass('glyphicon-time');
                    status_elem.removeClass('glyphicon-search');
                    status_elem.removeClass('glyphicon-hourglass');
                    status_elem.removeClass('glyphicon-ok');
                    status_elem.addClass('glyphicon-exclamation-sign');
                })
        }, 500)
    })
}

var addRelation = function() {
    // Appends another Relation row, and corresponding formset.
    cloneMore('.form_table_row:last', 'form');
    $('.autocomplete').each(function() {
        var pos = 'noun';
        if (this.id.indexOf('predicate') > -1) {
            pos = 'verb';
        }
        bindAutocomplete($('#' + this.id), pos);
    });
    bindTypeField();
}

bindTypeField();

$('#add-relation-button').on('click', function() {
    addRelation();
})

$('.autocomplete').each(function() {
    var pos = 'noun';
    if (this.id.indexOf('predicate') > -1) {
        pos = 'verb';
    }
    bindAutocomplete($('#' + this.id), pos);
});


var searchPromise = null;

// var conceptSearch =


// source: function( request, response ) {
//     $(this).addClass('ajax-loading');
//     $.getJSON(BASE_URL + "/rest/concept/search", {
//         search: extractLast( request.term ),
//         pos: pos,
//         remote: true,
//     }, function(data){
//         $(this).removeClass('ajax-loading');
//         response(data.results);
//     } );
// },
