angular.module('annotationApp')
        .controller('RelationTemplateSearchController',
            ['$scope', 'selectionService', 'RelationTemplate', 'RelationSet', 'Concept',
            function($scope, selectionService, RelationTemplate, RelationSet, Concept) {

    $scope.search = function() {
        $scope.relation_templates = RelationTemplate.query({search: $scope.query}).$promise.then(function(data){
            $scope.relation_templates = data.templates;
        });
    }

    $scope.select = function(rt) {
        rt.fields.forEach(function(field) {
            field.placeholder = field.concept_label;
            field.filled = false;
        });
        $scope.relation_template = rt;
        $scope.relation_create = true;
    }

    /**
      * Indicate whether to disable the RelationTemplate search input.
      *  TODO: do we really need this?
      */
    $scope.relationTemplateSearchInputLocked = function() {
        return ($scope.relation_create);
    }

    $scope.highlightAppellations = function(appellations) {
        selectionService.unhighlightAppellations();
        appellations.forEach(selectionService.highlightAppellation);
    }

    $scope.startCreatingRelation = function() {
        // TODO: do we need both of these?
        $scope.relation_create = true;
        $scope.hideRelationCreate = false;

        // Just in case the user has already selected some words...
        selectionService.releaseWords();
        selectionService.releaseAppellations();

        // Keep selected appellations highlighted.
        selectionService.persistHighlighting = true;

    }
    $scope.$on('startCreatingRelation', $scope.startCreatingRelation);

    $scope.hideRelationSearch = function() {
        return ($scope.relation_template.id != undefined | !$scope.relation_create);
    }

    $scope.reset = function() {
        RelationTemplate.list().$promise.then(function(data) {
            $scope.relation_templates = data.templates;
        });

        RelationSet.list().$promise.then(function(data) {
            $scope.relations = data.results;
        });
        $scope.relation_template = {};
        // TODO: do we need both of these?
        $scope.relation_create = false;
        $scope.hideRelationCreate = true;

        selectionService.persistHighlighting = false;
        selectionService.unhighlightAppellations();
    }

    $scope.isReadOnly = function(field) {
        return (field.evidence_required | field.filled);
    }

    $scope.conceptSearch = function(field) {
        if (field.query.length > 2) {
            field.options = Concept.query({
                search: field.query,
                pos: 'all',
                typed: field.concept_id,
                remote: true,
            }).$promise.then(function(data) {
                field.options = data;
            });
        };
    }

    $scope.isSearching = function(field) {
        if (field.options !== undefined) {
            if (field.options.length > 0) {
                return true;
            }
        }
        return false;
    }

    $scope.selectConcept = function(field, option) {
        field.selected = option;
        field.options = [];
        field.placeholder = option.label;
        field.filled = true;
    }

    /**
      * Evaluate whether or not all of the relation fields have been filled in.
      */
    $scope.allFieldsFilled = function() {
        // This will get called well before the user selects a relationtemplate.
        if ($scope.relation_template.fields) {
            var filled = true;
            $scope.relation_template.fields.forEach(function(field) {
                if (!field.filled) { filled = false; }
            });
            return filled;
        } else {
            // No relation template has been selected, so just bail.
            return false;
        }
    }

    // Once all of the fields are filled, the user can click the "create" button
    //  to submit the relation to the database.
    $scope.createRelation = function() {
        // Assemble data from all fields into a single payload.
        $scope.relation_template.occursIn = TEXTID;
        $.post('/relationtemplate/' + $scope.relation_template.id + '/create/',
               JSON.stringify($scope.relation_template),
               function(data) {
                   $scope.reset();
               });

        // Update relation list.
    }

    $scope.reset();     // Initialize.

    $(document).keydown(function(event) {
        if(event.which == 27) {     // ESC key.
            $scope.reset();
        }
    });
}]);


// Controls the appellation creation modal during the relation creation process.
angular.module('annotationApp').controller('AppellationModalInstanceController',
        function ($scope, $uibModalInstance, data) {

    $scope.selectedText = data.selectedText;
    $scope.selectedWords = data.selectedWords;
    $scope.conceptType = data.conceptType;

    $scope.ok = function () {
        $uibModalInstance.close();
    };

    $scope.cancel = function () {
        $uibModalInstance.dismiss('cancel');
    };

    // When the appellationController inside the modal finishes creating an
    //  Appellation, we close the modal.
    $scope.$on('appellationCreated', $scope.ok);
});



// Each field is controlled by a separate RelationTemplateFieldController instance.
angular.module('annotationApp').controller('RelationTemplateFieldController',
        ['$scope', 'selectionService', '$uibModal', 'Type',
        function($scope, selectionService, $uibModal, Type) {
    $scope.fielddata = {};
    $scope.field.filled = false;
    $scope.alert = false;

    $scope.showAlert = function(message) {
        $scope.alert = message;
    }

    $scope.resetAlert = function() {
        $scope.alert = false;
    }

    $scope.reset = function() {
        $scope.highlight = false;
        $scope.field.appellation = null;
        $scope.fielddata = {};
        $scope.field.filled = false;
        $scope.alert = false;
        $scope.clearFieldHighlights();
    }

    /**
      *   Remove field highlighting.
      */
    $scope.clearFieldHighlights = function() {
        $('.relation-field-input-group').removeClass('has-success');
    }

    $scope.highlightField = function() {
        $scope.clearFieldHighlights();
        $("#input-group-" + $scope.field.part_id + "_" + $scope.field.part_field).addClass('has-success');

    }

    /**
      * Once the user has filled a field, the addon icon for that field should
      * indicate that fact.
      */
    $scope.iconClass = function() {
        if ($scope.field.filled) {
            return 'glyphicon-ok evidence-filled';
        } else {
            return 'glyphicon-edit';
        }
    }

    /**
      * The appellation modal allows the user to create a new appellation. This
      *  is just like the appellation creation process in the appellation tab,
      *  except that we don't want the user to have to switch tabs a lot during
      *  the process of creating a relation.
      */
    $scope.openAppellationModal = function(data) {
        var modalInstance = $uibModal.open({
            animation: $scope.animationsEnabled,
            templateUrl: 'appellationModalContent.html',
            controller: 'AppellationModalInstanceController',
            resolve: {      // Angular is weird sometimes.
                data: function () {
                    return data;
                }
            }
        });

        // Don't need this right now, but maybe later. When an appellation is
        //  created, the selectionService automatically selects and succeeds,
        //  which fulfills the appellation expectation that we set in
        //  expectEvidence(). So it is not necessary for the modal to pass data
        //  back here.
        modalInstance.result.then(function () {
            // Success
        }, function () {
            // Fail
        });
    };

    // We don't use this at the moment, but maybe later.
    $scope.toggleAnimation = function () {
        $scope.animationsEnabled = !$scope.animationsEnabled;
    };

    /**
      *  Generate a string representation of the selected passage (for
      *   Concept.stringRep field).
      */
    var getStringRep = function(selector, delim) {
        var stringRep = $.map(selector, function(selem) {
            return selem.innerHTML;
        });
        return stringRep.join(delim);
    }

    /**
      *  Stitch word IDs together into a string suitable for Concept.tokenIds.
      */
    var getTokenIds = function(selector) {
        var tokenIds = [];
        selector.each(function () { tokenIds.push(this.id); });
        return tokenIds.join(',');
    }

    /**
      *  Set up word and appellation expectations for the field.
      */
    $scope.expectEvidence = function() {
        $scope.highlightField();

        selectionService.defer();   // We want precedence. Reenabled on success.
        // The appellation expectation should be fulfilled as soon as the user
        //  clicks on an appellation.
        selectionService.skipAppellationPopover = true;

        // TODO: this configuration works for fields that expect a full
        //  appellation (i.e. concept type field), but for fields that only
        //  require text evidence (i.e. specific concept field) we only need to
        //  implement a word expectation.

        // Concept type fields (TP) expect an appellation of a specific type,
        //  indicated by its ``concept_id`` attribute.
        if ($scope.field.type == 'TP') {
            // User can select an existing appellation.
            selectionService.expectAppellation(function(appellation) {
                if (appellation.interpretation_type == $scope.field.concept_id) {
                    // The Appellation interpretation has the correct Type.
                    $scope.field.appellation = appellation;
                    $scope.label = appellation.stringRep;
                    $scope.field.filled = true;

                    selectionService.highlightAppellation(appellation);
                } else {    // Appellation has the wrong Type for this field.
                    // TODO: This could be simplified with $q.
                    Type.get({id: appellation.interpretation_type}).$promise.then(function(selectedType) {
                        Type.get({id: $scope.field.concept_id}).$promise.then(function(expectedType) {
                            $scope.showAlert('This field requires an ' + expectedType.label + '; you selected an ' + selectedType.label + '.');
                        })
                    })

                }
                // The user must click on the field again to make another
                //  attempt.
                selectionService.resume();

                $scope.clearFieldHighlights();
            });

            // User can select text to create a new appellation. We use a modal
            //  here rather than the appellation tab, so that the user doesn't
            //  get lost going back and forth.
            selectionService.expectWords(function(data) {
                $scope.hideAppellationCreate = false;
                var modalData = {
                    selectedWords: data,
                    selectedText: getStringRep(data, ' '),
                    conceptType: $scope.field.concept_id,
                }
                $scope.openAppellationModal(modalData);
            });

        // The specific concept has already been given; the user need only
        //  provide text evidence.
        } else if($scope.field.type == 'CO') {
            selectionService.expectWords(function(data) {
                // The Appellation will be created when the Relation data are
                //  processed, so we just need to get the tokenIds and
                //  stringRep, and we're good to go.
                var stringRep = getStringRep(data, ' ');
                $scope.label = stringRep;
                $scope.field.filled = true;
                $scope.$apply();

                $scope.field.data = {
                    stringRep: stringRep,
                    tokenIds: getTokenIds(data),
                    occursIn: TEXTID,
                }
                $scope.clearFieldHighlights();
            }, function() {}, true);    // Release word selection automatically.
        }
    }

    $scope.reset();
}]);
