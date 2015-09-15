var app = angular.module('annotationApp', ['ngResource', 'ngSanitize', 'ui.bootstrap', 'angucomplete-alt', 'd3']);

app.config(function($httpProvider){
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

app.factory('Text', function($resource) {
    return $resource(BASELOCATION + '/rest/text/:id/');
});

app.factory('Appellation', function($resource) {
    return $resource(BASELOCATION + '/rest/appellation/:id/', {
        text: TEXTID
    }, {
        list: {
            method: 'GET',
            cache: true,
            headers: {'Content-Type': 'application/json'}
        },
        save: {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        }
    });
});

app.factory('Relation', function($resource) {
    return $resource(BASELOCATION + '/rest/relation/:id/', {
        text: TEXTID
    });
});

app.factory('Predicate', function($resource) {
    return $resource(BASELOCATION + '/rest/predicate/:id/', {
        text: TEXTID
    });
});

app.factory('TemporalBounds', function($resource) {
    return $resource(BASELOCATION + '/rest/temporalbounds/:id/');
});

app.factory('Concept', function($resource) {
    return $resource(BASELOCATION + '/rest/concept/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
        }
    });
});

app.factory('Type', function($resource) {
    return $resource(BASELOCATION + '/rest/type/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
        }
    });
});


app.factory('messageService', function($rootScope) {
    var service = {}
    service.newMessage = function(message, type) {
        var alertScope = angular.element($('#alerts')).scope();
        alertScope.closeAlert(0);
        alertScope.addAlert(message, type);
        return;
        // $rootScope.$broadcast('newMessage', message);
    }
    service.reset = function() {
        var alertScope = angular.element($('#alerts')).scope();
        alertScope.defaultAlert();
        if(!alertScope.$$phase) alertScope.$apply();
        return;
    }
    return service;
});

app.factory('selectionService', ["$rootScope", "appellationService", "messageService", "predicateService", "conceptService", "temporalBoundsService", "relationService", "errors", "$timeout", "$compile", "Type", "Concept", "$q", function($rootScope, appellationService, messageService, predicateService, conceptService, temporalBoundsService, relationService, errors, $timeout, $compile, Type, Concept, $q) {
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

        // var alertScope = angular.element($('#alerts')).scope();
        // alertScope.defaultAlert();
        // if(!alertScope.$$phase) alertScope.$apply();

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
                    authority: 'Vogon'
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
                title: 'How are these concepts related?',
                instructions: 'Select a predicate that best characterizes the relationship between the two concepts that you selected, based on your interpretation of the text. Most predicates are directional, so your first selection will be the subject of the relation and your second selection will be the object of the relation.',
                text: text,
                pos: 'verb',
                placeholder: 'Search for a predicate concept',
                baselocation: BASELOCATION,
                types: [],  // Concept types, for creation procedure.
                newConcept: {
                    pos: 'verb',
                    uri: 'generate',
                    authority: 'Vogon'
                }
            }

            Type.query().$promise.then(function(results) {
                settings.types = results;
            })
            angular.element($('#modalConcept')).scope().open(settings, function (modalData) {
                // var annotationScope = angular.element(document.getElementById('annotations')).scope();

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

                        var data = {    // Predicate creation payload.
                            interpretation: c.id,
                            stringRep: modalData.data.text.stringRep,
                            tokenIds: modalData.data.text.tokenIds,
                            occursIn: TEXTID,
                            createdBy: USERID,
                            inSession: 1,
                            asPredicate: true,
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
                                console.log(error);
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

        service.clearActions();

        var parent = $('<div>', {
            class: 'actionIcons panel',
        });
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

        $('#textContent').append(parent);
        parent.offset(calculatePosition(element));


        // Icons should track the element to which they are attached.
        $(window).resize(function() {
            parent.offset(calculatePosition(element));
        });
        if(!$rootScope.$$phase) $rootScope.$apply();
    }

    service.clearActions = function() {
        $('.actionIcons').remove();  // Remove any displayed icons.
    }

    return service;

}]);

app.factory('predicateService', ['$rootScope', 'Predicate', function($rootScope, Predicate) {
    return {
        createPredicate: function(data) {
            var predicate = new Predicate(data);
            return predicate.$save().then(function(a, rHeaders) {
                $rootScope.$broadcast('newPredicate', a);
                return a;
            });
        },
        getPredicate: function(id) {
            var service = this;
            return Predicate.get({id:id}, function(c) {
                /// hmmm...
            }).$promise.then(function(c){
                return c;
            });
        }
    };
}]);

app.factory('relationService', ['$rootScope', 'Relation', function($rootScope, Relation) {
    var relationService = {
        relationLabels: {},
        getRelation: function(relId) {  // Retrieve by ID.
            service = this;
            return Relation.get({id: relId}, function(c) {
                // hmmm...
            }).$promise.then(function(a) {
                return a;
            });
        },

        deleteRelation: function(data) {
            var service = this;

            service // Only the relation ID is passed in data, so we first
               .getRelation(data.id)     // retrieve the full relation.
               .then(function(relation) {
                    var mdata = {
                    	relation: data
                    };

                    // Ask the user to confirm (via modal) deletion.
                    angular.element($('#deleteRelationModal')).scope()
                        .open({relation:relation}, function(rdata) {
                            var relData = {
                                id: relation.id,
                            }

                            // Perform the deletion.
                            return Relation.delete(data).$promise.then(function() {
                                $rootScope.$broadcast('deleteRelation', relData);
                                service.getRelations(function() { null; });  // Refresh.
                                return relData;
                            });

                    });
               });
        },

        createRelation: function(data) {
            var relation = new Relation(data);
            return relation.$save().then(function(r, rHeaders) {
                rScope = angular.element($('#relations')).scope();
                rScope.relations.push(r);
                rScope.updateLabel(r);

                $rootScope.$broadcast('newRelation', r);
                return r;
            });
        },
        getRelations: function(callback) {
            service = this;

            return Relation.query().$promise.then(function(relations) {
                service.relations = relations;
                callback(relations);
                return relations;
            });
        },
    };

    return relationService;
}]);

app.factory('temporalBoundsService', ['$rootScope', 'TemporalBounds', function($rootScope, TemporalBounds) {
    return {
        createTemporalBounds: function(data) {
            var temporalbounds = new TemporalBounds(data);
            return temporalbounds.$save().then(function(t, rHeaders) {
                $rootScope.$broadcast('newTemporalBounds', t);
                return t;
            });
        },
    };
}]);

app.factory('conceptService', ['$rootScope', 'Concept', function($rootScope, Concept) {
    return {
        getConcept: function(id) {
            var service = this;
            return Concept.get({id:id}, function(c) {
                /// hmmm...
            }).$promise.then(function(c){
                return c;
            });
        }
    };
}]);

app.factory('appellationService', ['$rootScope', 'Appellation', function($rootScope, Appellation) {
    return {
        appellations: [],
        appellationHash: {},
        getAppellations: function(callback) {
            var service = this;

            return Appellation.query().$promise.then(function(appellations) {
                service.appellations = appellations;

                appellations.forEach(function(a) {
                    if(service.appellationHash[a.interpretation] == undefined) {
                        service.appellationHash[a.interpretation] = [];
                    }
                    service.appellationHash[a.interpretation].push(a);
                });
                callback(appellations);
                return appellations;
            });
        },
        getAppellation: function(appId) {  // Retrieve by ID.
            service = this;
            return Appellation.get({id: appId}, function(c) {
                // hmmm...
            }).$promise.then(function(a) {
                return a;
            });
        },
        getAppellationIndex: function(appId) {  // Retrieve by ID.
            var foundIndex;
            service.appellations.forEach(function(appellation, index) {
                if (String(appellation.id) == String(appId)) foundIndex = index;
            });
            return foundIndex;
        },
        createAppellation: function(data) {
            var appellation = new Appellation(data);
            var service = this;

            return appellation.$save().then(function(a, rHeaders) {
                service.appellations.push(a);
                if(service.appellationHash[a.interpretation] == undefined) {
                    service.appellationHash[a.interpretation] = [];
                }
                service.appellationHash[a.interpretation].push(a);
                $rootScope.$broadcast('newAppellation', a);
                return a;
            });
        },
        deleteAppellation: function(data) {
            var service = this;

            service // Only the appellation ID is passed in data, so we first
               .getAppellation(data.id)     // retrieve the full appellation.
               .then(function(appellation) {
                    var mdata = {
                    	appellation: data
                    };

                    // Ask the user to confirm (via modal) deletion.
                    angular.element($('#deleteAppellationModal')).scope()
                        .open({appellation:appellation}, function(rdata) {
                            var appData = {
                                id: appellation.id,
                                tokenIds: appellation.tokenIds,
                                stringRep: appellation.stringRep
                            }

                            // Perform the deletion.
                            return Appellation.delete(data).$promise.then(function() {
                                $rootScope.$broadcast('deleteAppellation', appData);
                                service.getAppellations(function() { null; });  // Refresh.
                                return appData;
                            });

                    });
               });
        }
    };
}]);

app.controller('ActionsController', function($scope, $position) {

});

app.controller('AlertController', function ($scope, $sce) {
    $scope.defaultAlert = function() {
        $scope.alerts = [{message: 'Click on a word to get started.'}];
    };
    $scope.defaultAlert();

    $scope.clearAlerts = function() {
        $scope.alerts = [];
    }

    $scope.addAlert = function(message, type) {
        $scope.alerts.push({type: type, message: $sce.trustAsHtml(message)});
    };

    $scope.closeAlert = function(index) {
        $scope.alerts.splice(index, 1);
    };

    $scope.newMessage = function(msg) {
        $scope.closeAlert(0);
        $scope.addAlert(msg);
    };
});

app.controller('ActionsController', function ($scope) {
    $scope.actions = [
        { icon: 'glyphicon-plus' },
        { icon: 'glyphicon-pencil' }
    ];
    $scope.isCollapsed = false;
});

app.controller('RelationsController', ['$scope', 'relationService', 'selectionService', 'conceptService', 'appellationService', '$q', 'predicateService', function($scope, relationService, selectionService, conceptService, appellationService, $q, predicateService) {
    $scope.relationLabels = {};

    $scope.deleteRelation = function(relation) {
        relationService.deleteRelation({id:relation.id});
    };

    $scope.updateLabel = function(relation) {
        // if ( $scope.relationLabels[relation.id] !== undefined) return;

        var sourceLabel, predicateLabel, targetLabel;

        $q.all([
            appellationService.getAppellation(relation.source),
            predicateService.getPredicate(relation.predicate),
            appellationService.getAppellation(relation.object)
        ]).then(function(data) {
            $q.all([
                conceptService.getConcept(data[0].interpretation),
                conceptService.getConcept(data[1].interpretation),
                conceptService.getConcept(data[2].interpretation)
            ]).then(function(cdata) {
                sourceLabel = cdata[0].label;
                predicateLabel = cdata[1].label;
                targetLabel = cdata[2].label;
                $scope.relationLabels[relation.id] = {
                    source: sourceLabel,
                    predicate: predicateLabel,
                    target: targetLabel
                }

            });
        });
    }
    $q.all([
        relationService.getRelations(function(relations) {
            $scope.relations = relations;
            relations.forEach($scope.updateLabel);
        })
    ]).then(function(data) {
        if(!$scope.$$phase) $scope.$apply();
    });

    var getRelationByID = function(relId) {
        for (i = 0; i < $scope.relations.length; i++) {
            if ($scope.relations[i].id === relId) return $scope.relations[i];
        }
    }

    $scope.$on('deleteRelation', function(event, r) {
        relationService.getRelations(function(){}).then(function(relations) {
            $scope.relations = relations;
            if(!$scope.$$phase) $scope.$apply();
        });
    });

    $scope.$on('deleteAppellation', function(event, r) {
        relationService.getRelations(function(){}).then(function(relations) {
            $scope.relations = relations;
            if(!$scope.$$phase) $scope.$apply();
        });
    });

    $scope.relationClick = function(relation) {
        var sourceElem = $('[appellation=' + relation.source + ']');
        var targetElem = $('[appellation=' + relation.object + ']');
        selectionService.reset();
        selectionService.highlight(sourceElem);
        selectionService.highlight(targetElem);
    }
}]);

app.controller('AppellationsController', ['$scope', '$rootScope', 'appellationService', 'selectionService', 'conceptService', 'Appellation', function($scope, $rootScope, appellationService, selectionService, conceptService, Appellation) {
    $scope.appellationLabels = {};

    $scope.deleteAppellation = function(appellation) {
        appellationService.deleteAppellation({id:appellation.id});
    };

    $scope.update = function() {
        appellationService.getAppellations(function() {}).then(function(appellations) {
            $scope.appellations = appellations;
            appellations.forEach(function(appellation) {
                conceptService
                    .getConcept(appellation.interpretation)
                    .then(function(concept) {
                         $scope.appellationLabels[appellation.id] = concept.label;
                    });
            });
        });
    }
    $scope.update();

    // Add a new appellation to the model.
    $scope.$on('newAppellation', function(event, appellation) {
        conceptService
            .getConcept(appellation.interpretation)
            .then(function(concept) {
                $scope.appellationLabels[appellation.id] = concept.label;
            });
        $scope.appellations.push(appellation);
    });

    // Remove a deleted appellation from the model.
    $scope.$on('deleteAppellation', function(event, a) {
        $scope.update();
        var index;  // Get index of appellation by ID.
        $scope.appellations.forEach(function(appellation, i) {
            if (String(appellation.id) == String(a.id)) index = i;
        });

        if (index) $scope.appellations.splice(index);
        if (!$scope.$$phase) $scope.$apply();
    });

    $scope.appellationClick = function(appId) {
        var appElem = $('[appellation=' + appId + ']');
        selectionService.clickSelectAppellation(appElem);
    }

}]);

app.controller('deleteConfirmModalController', ['$scope', '$modal', '$log', function($scope, $modal, $log) {
	$scope.animationsEnabled = true;

	$scope.open = function(data, callback) {
		var modalInstance = $modal.open({
			animation: $scope.animationsEnabled,
			templateUrl: 'deleteAppellationModalContent.html',
			controller: 'ModalInstanceController',
			resolve: {
                settings: function() {
                    return data;
                },
            }
		});

		modalInstance.result.then(callback, function(data) {
			console.log();
		});
	}
}]);

app.controller('ModalTemporalBoundsControl', function($scope, $modal, $log) {
    $scope.animationsEnabled = true;

    $scope.open = function(settings, callback) {
        settings.dateOptions = {

        };

        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'modalTemporalBounds.html',
            controller: 'ModalInstanceController',
            resolve: {
                settings: function() {
                    return settings;
                },
            }
        });

        modalInstance.result.then(callback, function() {
            $log.info('Modal dismissed at: ' + new Date());
        });
    }
});

app.controller('ModalConceptControl', function ($scope, $modal, $log) {
    $scope.animationsEnabled = true;
    $scope.open = function (settings, callback) {
        var modalInstance = $modal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'modalConcept.html',
            controller: 'ModalInstanceController',
            resolve: {
                settings: function() {
                    return settings;
                },
            }
        });

        modalInstance.result.then(callback, function () {
            $log.info('Modal dismissed at: ' + new Date());
        });
    };

    $scope.toggleAnimation = function () {
        $scope.animationsEnabled = !$scope.animationsEnabled;
    };
});

app.controller('ModalInstanceController', function ($scope, $modalInstance, settings) {
    $scope.okDisabled = false;
    $scope.createConceptDisabled = true;
    $scope.createConceptHidden = true;
    $scope.createConceptDetailsHidden = true;

    $scope.$watch('search', function(newVal, oldVal) {
        if (newVal !== undefined) {
            if (newVal.length > 2) $scope.createConceptDisabled = false;
            else $scope.createConceptDisabled = true;
        }
    }, true);

    $scope.assertUniqueChange = function () {
        if ($scope.assertUnique) $scope.createConceptDetailsHidden = false;
        else $scope.createConceptDetailsHidden = true;
    }

    $scope.startCreateConcept = function() {
        $scope.createConceptHidden = false;
        $scope.newConcept = settings.newConcept;
        $scope.newConcept.label = $scope.search;
        $scope.assertUnique = false;
    }

    $scope.selectConcept = function(c) {
        $scope.concept = c;
        $scope.okDisabled = false;
    };
    $scope.data = settings;

    $scope.ok = function () {
        $modalInstance.close($scope);
    };

    $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
    };
});

app.controller('TextController', function($scope, $element, $sce, Text) {
    var textid = $($element).attr('textid');
    var text = Text.get({id:textid}, function() {    // TODO: not hardcoded!!
        $scope.textContent = $sce.trustAsHtml(text.tokenizedContent);
    });


});

app.directive('escapeKey', function (selectionService) {
    return function (scope, element, attrs) {
        element.bind("keydown keypress", function (event) {
            if(event.which === 27) {
                event.preventDefault();
                selectionService.reset();
            }
        });
    };
});

app.directive('ngEnter', function($document) {
    return {
        scope: {
            ngEnter: "&"
        },
        link: function(scope, element, attrs) {
            var enterWatcher = function(event) {
                if (event.which === 13) {
                    scope.ngEnter();
                    if (!scope.$$phase) scope.$apply();
                    event.preventDefault();
                    $document.unbind("keydown keypress", enterWatcher);
                }
            };
            $document.bind("keydown keypress", enterWatcher);
        }
    }
});


app.directive('bindText', function($rootScope, appellationService, selectionService, Appellation) {
    var bindText = function() {
        $('word').on('click', function(e) {
            var target = $(e.target);

            if (target.is('.appellation')) {
                selectionService.clickSelectAppellation(target);
            } else {
                if (e.shiftKey) {
                    selectionService.clickSelectMultiple(target);
                } else {
                    // User has clicked on a non-appellation word.
                    selectionService.clickSelectWord(target);
                }
            }
        });
    }

    var highlight = function(a) {
        a.tokenIds.split(',').forEach(function(wordId) {
            var word = $('word#'+wordId);
            if (word.length > 0) {
                word.addClass("appellation");
                word.attr("appellation", a.id);
            }
        });
    }

    var unHighlight = function(a) {
        a.tokenIds.split(',').forEach(function(wordId) {
            var word = $('word#' + wordId);
            if (word.length > 0) {
                word.removeClass("appellation");
                word.attr("appellation", null);
            }
        });
    };

    return function(scope, element, attrs) {
        scope.$watch("textContent", function(value) {
            bindText();     // TODO: make more angular.

            // Highlight existing appellations.
            appellationService.getAppellations(function(appellations) {
                appellations.forEach(highlight);
            });
        });

        $rootScope.$on('newAppellation', function(event, a) {
            highlight(a);   // Highlight word(s).
            selectionService.deSelectAll();
            selectionService.clearActions();
        });

        $rootScope.$on('newPredicate', function(event, a) {
            selectionService.deSelectAll();
            selectionService.clearActions();
        });

        $rootScope.$on('deleteAppellation', function(event, a) {
            unHighlight(a);
            selectionService.deSelectAll();
            selectionService.clearActions();
        });
    }
});

app.factory("errors", function($rootScope, messageService, $timeout){
    return {
        catch: function(message){
            // return function(reason) {
            messageService.newMessage(message, 'danger');
            $timeout(messageService.reset, 3000);
            // var alertScope = angular.element($('#alerts')).scope();
            // alertScope.addAlert('danger', message);
            return;
            // };
        }
    };
});

app.directive('d3Network', ['d3Service', '$rootScope', 'appellationService', 'relationService', 'conceptService', 'selectionService', '$q', 'messageService', function(d3Service, $rootScope, appellationService, relationService, conceptService, selectionService, $q, messageService) {
    return {
        scope: {
            'graph': '='
        },
        restrict: 'EA',
        link: function(scope, element, attrs) {

            d3Service.d3().then(function(d3) {
                var linkDistance = 100;
                var height = 398;
                var margin = {top: 0, right: 1, bottom: 0, left: 1}
                    , width = parseInt(d3.select('#networkVis').style('width'), 10)
                    , width = width - margin.left - margin.right
                    , percent = d3.format('%');

                d3.select(window).on('resize', resize);

                function resize() {
                    // Update size of visualization as parent element resizes.

                    width = parseInt(d3.select('#networkVis').style('width'), 10);
                    width = width - margin.left - margin.right;
                    svg.attr('height', (height + margin.top + margin.bottom) + 'px')
                        .attr('width', (width + margin.left + margin.right) + 'px');
                }

            	var force = d3.layout.force()
            	    .charge(-200)
            	    .linkDistance(linkDistance)
            	    .size([width, height]);

            	var svg = d3.select(element[0]).append("svg")
            	    .attr("width", width)
            	    .attr("height", height);

                scope.nodes = [];
                scope.edges = [];

                scope.findNode = function (id) {
                    for (var i=0; i < scope.nodes.length; i++) {
                        if (scope.nodes[i].id === id)
                            return scope.nodes[i];
                    };
                }

                scope.findNodeIndex = function (id) {
                    for (var i=0; i < scope.nodes.length; i++) {
                        if (scope.nodes[i].id === id)
                            return i;
                    };
                }

                scope.findEdgeIndex = function(sourceId, targetId) {
                    for (var i=0; i < scope.edges.length; i++) {
                        if ((scope.edges[i].source.id === sourceId) && (scope.edges[i].target.id === targetId)) {
                            return i;
                        }
                    }
                }

                scope.removeNode = function (id) {
                    var i = 0;
                    var n = scope.findNode(id);
                    while (i < scope.edges.length) {
                        if ((scope.edges[i]['source'] === n)||(scope.edges[i]['target'] == n)) scope.edges.splice(i,1);
                        else i++;
                    }
                    var index = scope.findNodeIndex(id);
                    if(index !== undefined) {
                        scope.nodes.splice(index, 1);
                        scope.update();
                    }
                }

                scope.removeEdge = function(sourceId, targetId) {
                    var edgeId = scope.findEdgeIndex(sourceId, targetId);
                    if (edgeId !== undefined) {
                        scope.edges.splice(edgeId, 1);
                    }
                    scope.update();
                }

                scope.addNode = function(appellation) {
                    // scope.nodes.push(node);
                    conceptService
                        .getConcept(appellation.interpretation)
                        .then(function(concept) {
                            var n = scope.findNode(concept.id);
                            if (n == undefined) scope.nodes.push(concept);
                        });
                    scope.update();
                }

                scope.addEdge = function (relation) {
                    $q.all([
                        appellationService.getAppellation(relation.source),
                        appellationService.getAppellation(relation.object),
                    ]).then(function(data) {
                        $q.all([
                            conceptService.getConcept(data[0].interpretation),
                            conceptService.getConcept(data[1].interpretation),
                        ]).then(function(cdata){
                            var sourceNode = scope.findNodeIndex(cdata[0].id);
                            var targetNode = scope.findNodeIndex(cdata[1].id);
                            if((sourceNode !== undefined) && (targetNode !== undefined)) {
                                scope.edges.push({"source": sourceNode, "target": targetNode, "relation": relation});
                                scope.update();
                            }
                        });
                    });
                }

                scope.highlightNode = function(node) {
                    d3.select('#node_' + node.id).classed("nodeSelected", true);
                }

                scope.selectNode = function(node) {
                    scope.highlightNode(node);
                    selectionService.deHighlightAll();
                    selectionService.deSelectAll();
                    selectionService.clearActions();
                    messageService.reset();

                    appellationService.appellationHash[node.id].forEach(function(appellation) {
                        selectionService.highlight($('[appellation='+appellation.id+']'));
                    });
                }
                scope.unselectNodes = function() {
                    d3.select('.nodeSelected').classed("nodeSelected", false);
                }

                scope.update = function() {
                    svg.selectAll('*').remove();

                    var edge = svg.selectAll(".edge")
                        .data(scope.edges)
                        .enter().append("line")
                        .attr("class", "edge")
                        .attr('marker-end','url(#arrowhead)')
                        .style("stroke", "black")
                        .style("stroke-width", function(d) { return Math.sqrt(d.value); });

                    rScope = angular.element($('#relations')).scope();

                    var node = svg.selectAll(".node")
                        .data(scope.nodes)
                        .enter().append("g")
                            .attr("class", "node")
                            .attr("id", function(d) { return 'node_'+d.id; })
                            .call(force.drag);

                    node.append("circle")
                        .attr("r", 8)
                        .attr("class", "node");

                    node.append("text")
                        .attr('dx', 12)
                        .attr('dy', "0.35em")
                        .attr("class", "nodeLabel")
                        .text(function(d) { return d.label; });

                    node.on("click", function(n) {
                        scope.unselectNodes();
                        scope.selectNode(n);
                    });

                    force
                        .nodes(scope.nodes)
                        .links(scope.edges)
                        .start();

                    force.on("tick", function() {
                        edge.attr("x1", function(d) { return d.source.x; })
                            .attr("y1", function(d) { return d.source.y; })
                            .attr("x2", function(d) { return d.target.x; })
                            .attr("y2", function(d) { return d.target.y; });
                        node.attr("transform", function(d) {
                            return "translate(" + d.x + "," + d.y + ")";
                        });

                        edgepaths.attr('d', function(d) {
                            return 'M '+d.source.x+' '+d.source.y+' L '+ d.target.x +' '+d.target.y;
                        });

                        edgelabels.attr('transform',function(d,i){
                            if (d.target.x<d.source.x) {
                                bbox = this.getBBox();
                                rx = bbox.x+bbox.width/2;
                                ry = bbox.y+bbox.height/2;
                                return 'rotate(180 '+rx+' '+ry+')';
                            } else {
                                return 'rotate(0)';
                            }
                        });
                    });

                    var edgepaths = svg.selectAll(".edgepath")
                        .data(scope.edges)
                        .enter()
                        .append("path")
                        .attr({
                            "d": function(d) {
                                    return 'M '+d.source.x+' '+d.source.y+' L '+ d.target.x +' '+d.target.y;
                                },
                            'class':'edgepath',
                             'fill-opacity':0,
                             'stroke-opacity':0,
                             'fill':'blue',
                             'stroke':'red',
                             'id':function(d,i) {return 'edgepath'+i; }
                         })
                          .style("pointer-events", "none");

                    var edgelabels = svg.selectAll(".edgelabel")
                      .data(scope.edges)
                      .enter()
                      .append('text')
                      .style("pointer-events", "none")
                      .attr({'class':'edgelabel',
                             'id':function(d,i){return 'edgelabel'+i},
                             'dx': linkDistance/4,
                             'dy':0,
                             'font-size':10,
                             'fill':'#aaa'});

                    edgelabels.append('textPath')
                      .attr('xlink:href',function(d,i) {return '#edgepath'+i})
                      .style("pointer-events", "none")
                      .text(function(d) {
                          return rScope.relationLabels[d.relation.id].predicate;
                      });

                  svg.append('defs').append('marker')
                          .attr({'id':'arrowhead',
                                 'viewBox':'-0 -5 10 10',
                                 'refX':15,
                                 'refY':0,
                                 //'markerUnits':'strokeWidth',
                                 'orient':'auto',
                                 'markerWidth':10,
                                 'markerHeight':10,
                                 'xoverflow':'visible'})
                          .append('svg:path')
                              .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
                              .attr('fill', '#ccc')
                              .attr('stroke','#ccc');


                }

                scope.updateData = function() {
                    scope.nodes = [];
                    scope.edges = [];
                    return appellationService.getAppellations(function(appellations){
                        appellations.forEach(function(appellation) {
                            scope.addNode(appellation);
                        });
                    }).then(function(d) {
                        relationService.getRelations(function(relations){
                            relations.forEach(function(relation) {
                                scope.addEdge(relation);
                            });
                        }).then(function(d) {
                            scope.update();
                        });
                    });
                }
                scope.updateData();


                $rootScope.$on('newAppellation', function(event, appellation) {
                    scope.addNode(appellation);
                });

                $rootScope.$on('newRelation', function(event, r) {
                    scope.addEdge(r);
                });

                $rootScope.$on('deleteAppellation', function(event, r) {
                    scope.updateData();
                });

                $rootScope.$on('deleteRelation', function(event, r) {
                    scope.updateData();
                });
            });
        },
    }
}]);
