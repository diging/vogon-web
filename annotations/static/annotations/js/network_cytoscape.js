

// While awaiting a response to an ajax request, a spinner is shown in the
//  network visualization panel.
var opts = {
  lines: 13 // The number of lines to draw
, length: 21 // The length of each line
, width: 14 // The line thickness
, radius: 42 // The radius of the inner circle
, scale: 1 // Scales overall size of the spinner
, corners: 1 // Corner roundness (0..1)
, color: '#297CA6' // #rgb or #rrggbb or array of colors
, opacity: 0.25 // Opacity of the lines
, rotate: 0 // The rotation offset
, direction: 1 // 1: clockwise, -1: counterclockwise
, speed: 1 // Rounds per second
, trail: 62 // Afterglow percentage
, fps: 20 // Frames per second when using setTimeout() as a fallback for CSS
, zIndex: 2e9 // The z-index (defaults to 2000000000)
, className: 'spinner' // The CSS class to assign to the spinner
, top: '50%' // Top position relative to parent
, left: '50%' // Left position relative to parent
, shadow: false // Whether to render a shadow
, hwaccel: false // Whether to use hardware acceleration
, position: 'absolute' // Element positioning
}

$(networkContainerSelector).spin(opts);    // Start spinner in the network display panel.

var hideConcept = function(data) {
    $('.selection-details-panel').css("display", "none");
}

var displayConcept = function(data) {
    $('.selection-details-panel').css("display", "block");
    $('#elem-type-selected').text('node');
    $('#concept-href').attr('href', '/concept/' + data.concept_id + '/');
    $('#concept-label').text(data.label);
    $('#concept-uri').text(data.uri);
    $('#concept-description').text(data.description);
}

var displayRelation = function(source_data, target_data) {
    $('.selection-details-panel').css("display", "block");
    $('#elem-type-selected').text('edge');
    $('#concept-href').attr('href', '/relations/' + source_data.concept_id + '/' + target_data.concept_id + '/');
    $('#concept-label').text(source_data.label + ' & ' + target_data.label);
    $('#concept-uri').text('');
    $('#concept-description').text('');
}

var displayTexts = function(texts) {
    $('#text-list').empty();
    $('#concept-text-list-title').text('Occurs in the following texts');
    texts.forEach(function(text) {
        $('#text-list')
            .append('<tr><td class="text-small"><a href="/text/' + text.id + '/">' + text.title + '</a></td></tr>');
    });
}

var displayRelations = function(relations, source_data, target_data) {
    $('#text-list').empty();
    $('#concept-text-list-title').text('Are related in the following ways');
    relations.forEach(function(relation) {
        $('#text-list')
            .append('<tr><td class="text-small"><a href="/relations/' + source_data.concept_id + '/' + target_data.concept_id + '/">' + relation.concept_label + ' </a><span class="label label-default">' + relation.count + '</span><p class="text text-muted text-small">'+ relation.description +'</p></td></tr>');
    });
}


var loadNetwork  = function(e, params, callback) {
    var cy;

    if (!params) {
        params = '';
    }

    // Must set networkEndpoint in the dependant template.
    $.ajax(networkEndpoint, {
        // Pass filtering options (e.g. text, creator, date ranges).
        data: params,

        // When the data is returned, generate an interative visualization
        //  using Cytoscape.js.
        success: function(data) {
            // Stop spinner when the data loads.
            $(networkContainerSelector).spin(false);

            // Normalize node and edge weights.
            var minEdgeWeight = 1.0;
            var maxEdgeWeight = 0.0;
            var minNodeWeight = 1.0;
            var maxNodeWeight = 0.0;


            data.elements.forEach(function(elem) {
                var weight = Number(elem.data.weight);
                if (elem.data.source) {  // Edge.
                    if (weight > maxEdgeWeight) maxEdgeWeight = weight;
                    if (weight < minEdgeWeight) minEdgeWeight = weight;
                } else {
                    if (weight > maxNodeWeight) maxNodeWeight = weight;
                    if (weight < minNodeWeight) minNodeWeight = weight;
                }
            });

            // If min and max are the same, cytoscape will throw a TypeError,
            //  so we decrement the min values just to be safe.
            minNodeWeight = Number(minNodeWeight.toPrecision(4)) - 1;
            maxNodeWeight = Number(maxNodeWeight.toPrecision(4));
            minEdgeWeight = Number(minEdgeWeight.toPrecision(4)) - 1;
            maxEdgeWeight = Number(maxEdgeWeight.toPrecision(4));

            cy = cytoscape({
                container: $(networkContainerSelector),
                elements: data.elements,

                minZoom: 0.2,
                maxZoom: 3,
                zoom: 1,
                panningEnabled: true,
                style: [    // The stylesheet for the graph.
                    {
                        // Node size is a function of topic prevalence.
                        selector: 'node',
                        style: {
                            'background-color': '#B74934',
                            'label': 'data(label)',
                            'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 15, 45)',
                            'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 15, 45)',
                            'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 8, 36)'
                        }
                    },
                    {
                        selector: 'node.connectedNodes',
                        style: {
                            'opacity': 1.0,
                            'border-color': '#AA9A66',
                            'border-width': 2,
                            'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 25, 55)',
                            'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 25, 55)',
                            'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 18, 52)'
                        }
                    },
                    {
                        selector: 'node.nonConnectedNodes',
                        style: {
                            'opacity': 0.5,
                        }
                    },
                    {
                        // When a node is selected, it should be slightly larger
                        //  and have a colored border.
                        selector: 'node:selected',
                        style: {
                            'border-color': '#AA9A66',
                            'border-width': 4,
                            'font-size': 'mapData(weight, ' + minNodeWeight + ', ' + maxNodeWeight + ', 35, 75)',
                            'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 60, 90)',
                            'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 60, 90)',
                        }
                    },
                    {
                        // Active nodes should be slightly larger.
                        selector: 'node:active',
                        style: {
                            'width': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 30, 60)',
                            'height': 'mapData(weight, ' + minNodeWeight  + ', ' + maxNodeWeight + ', 30, 60)',
                        }
                    },
                    {
                        // Edge weight is a function of nPMI.
                        selector: 'edge',
                        style: {
                            'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 0.5, 6)',
                            'opacity': 'mapData(weight, 0.01, 0.5, 0.1, 1)',
                            'line-color': '#67655D',
                            'target-arrow-color': '#ccc',
                        },
                    },
                    {
                        selector: 'edge.connectedEdge',
                        style: {
                            'opacity': 1,
                            'line-color': '#AA9A66',
                            'z-index': 500,
                            'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 1, 12)',
                        }
                    },
                    {
                        selector: 'edge.nonConnected',
                        style: {
                            'opacity': 0.2,
                        }
                    },
                    {
                        // A selected edge should be slightly thicker, and be colored a brighter color.
                        selector: 'edge:selected',
                        style: {
                            'width': 'mapData(weight, ' + minEdgeWeight  + ', ' + maxEdgeWeight + ', 2, 8)',
                            'opacity': 1,
                            'line-color': '#AA9A66',
                        }
                    },
                ],



                layout: {
                  name: 'preset',
                  positions: function(n) { return n._private.data.pos; },
                }
            });

            var clearConnected = function() {
                cy.elements('edge').edges().removeClass('connectedEdge');
                cy.elements('edge').edges().removeClass('nonConnected');
                // cy.elements('edge').edges().unselect();
                cy.elements('node').nodes().removeClass('connectedNodes');
                cy.elements('node').nodes().removeClass('nonConnectedNodes');
                // cy.elements('node').nodes().unselect();
            }

            cy.on('select', 'node', function(event) {
                var node = event.cyTarget;
                displayConcept(node._private.data);
                displayTexts(node._private.data.texts);

                // Highlight connected nodes and edges.
                clearConnected();
                var directlyConnected = node.neighborhood();
                var nonConnected = cy.elements().difference( directlyConnected );

                directlyConnected.nodes().addClass('connectedNodes');
                nonConnected.nodes().addClass('nonConnectedNodes');
                nonConnected.edges().addClass('nonConnected');
                node.removeClass('nonConnectedNodes');
                node.neighborhood('edge').edges().addClass('connectedEdge');

                $('#networkAlert').css('display', 'none');
            });

            cy.on('select', 'edge', function(event) {
                var edge = event.cyTarget;
                var source = edge._private.source,
                    target = edge._private.target;

                displayRelation(source._private.data, target._private.data);
                displayRelations(edge._private.data.relations, source._private.data, target._private.data);

                $('#networkAlert').css('display', 'none');
                clearConnected();
            });
            cy.on('unselect', 'node', function(event) {
                hideConcept();

                clearConnected();
                $('#networkAlert').css('display', 'block');
            });
            cy.on('unselect', 'edge', function(event) {
                hideConcept();

                clearConnected();
                $('#networkAlert').css('display', 'block');
            });

            if (callback) {
                callback(cy);
            }

        }

    });
    var resizeGraph = function() {
        // var targetHeight = Number($('.action-body').css('max-height').replace('px', ''));
        // $('#networkVis').height(targetHeight - 10);
        cy.resize();
        cy.fit();
    }
    $(window).resize(resizeGraph);



}


$('body').ready(function(e) {
    if (typeof(networkParams) == 'undefined') {
        networkParams = window.location.search.substring(1);
    }

    if (typeof(networkCallback) == 'undefined') {
        networkCallback = function() {};
    }

    loadNetwork(e, networkParams, networkCallback);
});
