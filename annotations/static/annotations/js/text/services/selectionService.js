/**
  * The selectionService is responsible for handling
  *
  **/
app.factory('selectionService',
            ["$rootScope", "appellationService", "messageService",
            "predicateService", "conceptService", "temporalBoundsService",
            "relationService", "errors", "$timeout", "$compile", "Type",
            "Concept", "$q",
             function($rootScope, appellationService, messageService, predicateService,
                      conceptService, temporalBoundsService, relationService, errors,
                      $timeout, $compile, Type, Concept, $q) {
    var service = {
        ignoreWordClick: false,
        ignoreAppellationClick: false,
        expectTarget: false,
        noAppellation: false,
    };

    /**
      * Reset service to default state.
      */
    service.reset = function() {
        service.ignoreWordClick = false;
        service.ignoreAppellationClick = false;
        service.expectTarget = false;
        service.noAppellation = false;
        service.source = null;
        service.target = null;
        service.predicate = null;
        service.sourceConcept = null;
        service.targetConcept = null;
        service.predicateConcept = null;

        service.deSelectAll();
        service.deHighlightAll();
        service.clearActions();

    }

    var getStringRep = function(selector, delim) {
        var stringRep = $.map(selector, function(selem) {
            return selem.innerHTML;
        });
        return stringRep.join(delim);
    }

    var editAppellationIcon = {type: 'glyphicon-pencil', id:'edit'}

    var deleteAppellationIcon = {
        type: 'glyphicon-remove',
        id: 'remove',
        tooltip: 'Delete this appellation.',
        action: function(e) {
            var data = {
                id: service.getCurrentAppellationID()
            }
            appellationService.deleteAppellation(data);
        }
    }

    var createAppellationIcon = {
        type:'glyphicon-plus',
        id:'create',
        action: function(e) {
            var stringRep = getStringRep(service.selected, ' ');
            var tokenIds = $.map(service.selected, function(selem) {
                return selem.id;
            });
            var text = {
                stringRep: stringRep,
                tokenIds: tokenIds.join(',')
            };

            // TODO: simplify this -vv-
            var settings = {
                title: 'What is this?',
                instructions: 'Please select the concept (e.g. person, place, institution, organism) to which your text selection refers.',
                text: text,
                pos: 'noun',
                placeholder: 'Search for a concept',
                baselocation: BASELOCATION,
                types: [],  // Concept types, for creation procedure.
                newConcept: {
                    pos: 'noun',
                    uri: 'generate',
                    authority: 'Vogon',
                    resolved: true
                }
            }
            Type.query().$promise.then(function(results) {
                settings.types = results;
            })

            angular.element($('#modalConcept')).scope().open(settings, function(modalData) {
                var annotationScope = angular.element(document.getElementById('annotations')).scope();

                // This is asynchronous, as we may have to create a new Concept.
                var getConcept = function() {
                    return $q(function(resolve, reject) {
                        var concept = null;
                        if (modalData.newConcept) {
                            modalData.newConcept.typed = modalData.newConcept.typed.id;
                            concept = new Concept(modalData.newConcept);
                            concept.$save().then(function(c) {
                                resolve(c);
                            });
                        } else {
                            concept = modalData.concept.originalObject;
                            resolve(concept);
                        }

                    })
                }
                var promise = getConcept();
                promise.then(function(c) {
                    var data = {    // Appellation creation payload.
                        interpretation: c.id,
                        stringRep: modalData.data.text.stringRep,
                        tokenIds: modalData.data.text.tokenIds,
                        occursIn: TEXTID,
                        createdBy: USERID,  // TODO: remove.
                        inSession: 1
                    }

                    appellationService
                        .createAppellation(data)
                        .then(function(a) {
                            service.source = a;
                        })
                        .catch(function() {
                            service.reset();
                            errors.catch("Could not create appellation!");
                        });
                })

            });
        }
    }

    var createRelationIcon = {
        type: 'glyphicon-arrow-right',
        id: 'relation',
        action: function(e) {
            service.ignoreWordClick = true;
            service.expectTarget = true;
            service.clearActions();
            var alertScope = angular.element($('#alerts')).scope();
            alertScope.newMessage('Source: <span class="quotedText">' + service.sourceConcept.label + '</span>. Select a target appellation.');
            if(!alertScope.$$phase) alertScope.$apply();
        }
    }

    /**
      * Used to finalize a text selection.      glyphicon-calendar
      */
    var createPredicateIcon = {
        type: 'glyphicon-ok',
        id: 'predicate',
        action: function(e) {
            var stringRep = getStringRep(service.selected, ' ');
            var tokenIds = $.map(service.selected, function(selem) {
                return selem.id;
            });
            var text = {
                stringRep: stringRep,
                tokenIds: tokenIds.join(',')
            };
            var settings = {
                source_interpretation: null,
                target_interpretation: null,
                instructions: 'Select a predicate that best characterizes the relationship between the two concepts that you selected, based on your interpretation of the text.',
                text: text,
                pos: 'verb',
                placeholder: 'Search for a predicate concept',
                baselocation: BASELOCATION,
                types: [],  // Concept types, for creation procedure.
                newConcept: {
                    pos: 'verb',
                    uri: 'generate',
                    authority: 'Vogon'
                },
                controlling_verb: ''
            }

            Type.query().$promise.then(function(results) {
                settings.types = results;
            })

            Concept.get({id:service.source.interpretation}).$promise.then(function(result) {
                settings.source_interpretation = result;
            });
            Concept.get({id:service.target.interpretation}).$promise.then(function(result) {
                settings.target_interpretation = result;
            });
            angular.element($('#modalPredicate')).scope().open(settings, function (modalData) {

                    var getConcept = function() {
                        return $q(function(resolve, reject) {
                            var concept = null;
                            if (modalData.newConcept) {
                                // The user elected to create a brand-new
                                //  concept, rather than using one already in
                                //  the database.
                                modalData.newConcept.typed = modalData.newConcept.typed.id;
                                concept = new Concept(modalData.newConcept);
                                concept.$save().then(function(c) {
                                    resolve(c);
                                });
                            } else {
                                concept = modalData.concept.originalObject;
                                resolve(concept);
                            }

                        })
                    }

                    var promise = getConcept();
                    promise.then(function(c) {
                        var data = {    // Predicate creation payload.
                            interpretation: c.id,
                            stringRep: modalData.data.text.stringRep,
                            tokenIds: modalData.data.text.tokenIds,
                            occursIn: TEXTID,
                            createdBy: USERID,
                            inSession: 1,
                            asPredicate: true,
                            controlling_verb: modalData.controlling_verb,
                        }

                        predicateService
                            .createPredicate(data)
                            .then(function(predicate) {
                                service.predicate = predicate;
                                conceptService
                                    .getConcept(service.predicate.interpretation)
                                    .then(function(c) {
                                        service.predicateConcept = c;
                                        var tBsettings = {
                                            title: 'When did this relationship occur?',
                                            instructions: 'Select the date (to the greatest degree of precision) on which this relationship commenced or terminated, or the date on which you know the relationship to have existed. Do not provide any more information than what is substantiated by the text.',
                                            contextData: {
                                                sourceConcept: service.sourceConcept,
                                                predicateConcept: service.predicateConcept,
                                                targetConcept: service.targetConcept,
                                            },
                                        }
                                        angular.element($('#modalTemporalBounds')).scope().open(tBsettings, function(modalData) {
                                            var data = {};
                                            if (modalData.started) {
                                                data.start = [];
                                                if (modalData.started.year) data.start.push(modalData.started.year);
                                                if (modalData.started.month) data.start.push(modalData.started.month);
                                                if (modalData.started.day) data.start.push(modalData.started.day);
                                            }
                                            if (modalData.ended) {
                                                data.end = [];
                                                if (modalData.ended.year) data.end.push(modalData.ended.year);
                                                if (modalData.ended.month) data.end.push(modalData.ended.month);
                                                if (modalData.ended.day) data.end.push(modalData.ended.day);
                                            }
                                            if (modalData.occurred) {
                                                data.occur = [];
                                                if (modalData.occurred.year) data.occur.push(modalData.occurred.year);
                                                if (modalData.occurred.month) data.occur.push(modalData.occurred.month);
                                                if (modalData.occurred.day) data.occur.push(modalData.occurred.day);
                                            }

                                            var temporalBounds = temporalBoundsService.createTemporalBounds(data).then(function(t) {
                                                var relationData = {
                                                    source: service.source.id,
                                                    predicate: service.predicate.id,
                                                    object: service.target.id,
                                                    bounds: t.id,
                                                    occursIn: TEXTID,
                                                    createdBy: USERID,
                                                    inSession: 1,
                                                }

                                                // Last step: create the relation!
                                                relationService
                                                    .createRelation(relationData)
                                                    .then(function(r) {
                                                        messageService.newMessage('Created relation: <span class="quotedText">' + service.sourceConcept.label + ' - ' + service.predicateConcept.label + ' - ' + service.targetConcept.label + '</span>.', 'success');
                                                        service.reset();
                                                        $timeout(messageService.reset, 3000);
                                                    });
                                            });

                                        });

                                    });

                            })
                            .catch(function(error) {
                                service.reset();
                                errors.catch("Could not create predicate!");
                            });
                    });

            });
        }
    }

    service.select = function(selector) {
        if (service.selected) service.selected = service.selected.add(selector);
        else service.selected = selector;
        selector.addClass('selected');
    }

    service.highlight = function(selector) {
        selector.addClass('highlight');
    }

    service.deHighlight = function(selector) {
        selector.removeClass('highlight');
    }

    service.deHighlightAll = function() {
        $('.highlight').removeClass('highlight');
    }

    service.select_by = function(selection_string) {
        service.select($(selection_string));
    }

    service.isSelected = function(elem) {
        return service.selected.indexOf(elem) > -1;
    }

    service.deSelect = function(selector) {
        selector.removeClass('selected');
        selector.each(function(elem) {
            var index = service.selected.indexOf(elem);
            if (index > -1) service.selected.splice(index, 1);
        });
    }

    service.deSelectAll = function() {
        if (service.selected) service.selected.removeClass('selected');
        service.selected = null;
    }

    service.getCurrentAppellationID = function() {
        return service.selected.attr("appellation");
    }

    service.selectIntermediate = function(start, end) {
        // Select words between start and end. If start, end, or any
        // intermediate words are appellations, abort and clear all selections.
        var toSelect = start.nextUntil(end).add(start).add(end);

        if (toSelect.is('.appellation')) {  // Selection crosses an appellation.
            return false;
        }
        service.select(toSelect);   // Otherwise, select everything.
        return true;
    }

    service.clickSelectAppellation = function(target) {
        if (service.ignoreAppellationClick) return

        var targetElement, targetSelector, icons;
        targetSelector = $('[appellation=' + target.attr("appellation") + ']');
        targetElement = targetSelector.last();
        icons = [editAppellationIcon, deleteAppellationIcon, createRelationIcon];
        var networkScope = angular.element($('#network')).isolateScope();

        // Create a new relation.
        if (service.expectTarget) {
            service.relationSource = service.selected;
            service.relationTarget = targetSelector;
            service.expectTarget = false;
            service.ignoreWordClick = false;
            service.ignoreAppellationClick = true;
            service.noAppellation = true;

            service.highlight(service.relationSource);

            // Acquire the target appellation and its interpretation.
            appellationService
                .getAppellation(target.attr("appellation"))
                .then(function(a) {
                    service.target = a;
                    conceptService
                        .getConcept(service.target.interpretation)
                        .then(function(concept) {
                            service.targetConcept = concept;
                            messageService.newMessage('Select the word or passage that best describes the relationship between <span class="quotedText">' + service.sourceConcept.label + '</span> and <span class="quotedText">' + service.targetConcept.label + '</span>.');
                            service.deSelectAll();
                            service.highlight(service.relationTarget);

                            networkScope.highlightNode(concept);
                            // if(!networkScope.$$phase) networkScope.$apply();

                        });
                });
        } else {
            networkScope.unselectNodes();
            service.deHighlightAll();
            appellationService
                .getAppellation(target.attr("appellation"))
                .then(function(a) {
                    service.source = a;
                    conceptService
                        .getConcept(service.source.interpretation)
                        .then(function(concept) {
                            messageService.newMessage('You selected <span class="quotedText">' + concept.label + '</span>.');
                            service.sourceConcept = concept;

                            networkScope.highlightNode(concept);
                            // if((!networkScope.$$phase) networkScope.$apply();

                            return concept;
                        });
                });
            service.displayActions(targetElement, icons);
        }

        service.deSelectAll();
        service.select(target);
    }

    service.clickSelectMultiple = function(target) {
        // User can select multiple non-appellation words by holding
        //  the shift key.
        var first = service.selected.first();
        var last = service.selected.last();
        var index_target = $('word').index(target);
        var index_first = $('word').index(first);
        var index_last = $('word').index(last);
        var inter;

        // Select words between the new target word and either the
        //  start or end of the current selection.
        if (index_target < index_first) {       // Target is earlier.
            inter = service.selectIntermediate(target, first);
            targetElement = last;
        } else if (index_last < index_target) {     // Target is later.
            inter = service.selectIntermediate(last, target);
            targetElement = target;
        }

        // If multi-selection was aborted, the `targetElement` (where the icons)
        //  should appear should be the last element clicked (`target`).
        if (!inter){
            targetElement = target;
            service.deSelectAll();  // ...and we start a new selection.
        }

        service.select(target);
        service.displayWordActions(targetElement);
    }

    service.clickSelectWord = function(target) {
        if (service.ignoreWordClick) return

        targetElement = target;
        service.deSelectAll();  // New selection.

        var networkScope = angular.element($('#network')).isolateScope();
        if (!service.noAppellation) {
            service.deHighlightAll();
            networkScope.unselectNodes();
            if(!networkScope.$$phase) networkScope.$apply();
        }

        service.select(target);
        service.displayWordActions(targetElement);

        // TODO: figure out why this is necessary.
        var alertScope = angular.element($('#alerts')).scope();
        alertScope.newMessage('Hold the shift key and click on another word to select a series of words.');
        if(!alertScope.$$phase) alertScope.$apply();
        return;
    }

    service.displayWordActions = function(targetElement) {
        if (service.noAppellation) {
            icons = [createPredicateIcon];
        } else {
            icons = [createAppellationIcon];
        }
        service.displayActions(targetElement, icons);
        return;
    }

    /**
     * Display a set of icons next to DOM element.
     */
    service.displayActions = function(element, icons) {
        service.clearActions();

        /**
         * Get the appropriate offset for icons, based on the position of
         * element.
         */
        var calculatePosition = function(element) {
            var position = element.offset();
            position.left += element.width();
            position.top -= 5;
            return position;
        }

        var parent = $('<div>', {   // This will hold all of the icons.
            class: 'actionIcons panel',
        });

        // Add each icon to the parent container.
        icons.forEach(function(icon) {
            var elem = $("<button>", {
                class: "btn btn-primary btn-xs",
            });
            var iData = {
                class: "glyphicon " + icon.type,
                id:icon.id,
            };
            elem.append($("<span>", iData).on('click', icon.action));
            parent.append(elem);
        });

        var textScope = angular.element($('#textContent')).scope();
        textScope.addElement(parent, function(parent) {
            // Icons should track the element to which they are attached.
            $(window).resize(function() {
                parent.offset(calculatePosition(element));
            });

            // The initial position must take into account the distance that the
            // user has scrolled in #textContent.
            var pos = calculatePosition(element);
            pos.top += $('#textContent').scrollTop();
            parent.offset(pos);
        });
        // $('#textContent').append(parent);
    }

    service.clearActions = function() {
        $('.actionIcons').remove();  // Remove any displayed icons.
        $(window).off("resize");
    }

    return service;

}]);
