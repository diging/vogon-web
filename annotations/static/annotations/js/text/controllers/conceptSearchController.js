/**
  * The ConceptSearchController handles queries for, and creation of, concepts
  *  in the appellation creation process.
  */
app.controller('ConceptSearchController',
               ['$scope', 'Concept', 'Type', 'truncateFilter', function($scope, Concept, Type, truncateFilter) {
    $scope.assertUnique = false;
    $scope.concepts = [];
    $scope.pos = {
      id: 'noun',
      label: 'Noun'
    };
    $scope.pos_options = [{
      id: 'noun',
      label: 'Noun'
    }, {
      id: 'verb',
      label: 'Verb'
    }];

    $scope.search = function() {
        if ($scope.query.length > 2 & !$scope.creatingConcept) {
            var params = {search: $scope.query, pos: $scope.pos.id, typed: $scope.conceptType, remote: true}
            $scope.concepts = [];
            $scope.message = 'Searching...';
            Concept.query(params).$promise.then(function(data){
                $scope.concepts = data.results;
                $scope.message = null;
            });
        }
    }

    /**
      * The "selected" concept is available for appellation-related actions.
      */
    $scope.select = function(concept) {
        $scope.data.selectedConcept = concept;
        $scope.query = concept.label;
        $scope.concepts = [];
    }

    $scope.unselectConcept = function() {
        $scope.data.selectedConcept = null;
        $scope.query = '';
        $scope.concepts = [];
        $scope.concept = null;
    }

    /**
      * Clear search results, creation data, and unselect the current selected
      *  concept.
      */
    $scope.reset  = function() {
        $scope.concepts = [];
        $scope.newConcept = {};
        $scope.unselectConcept();
    }

    /**
      *  Indicate whether or not the search input should be disabled.
      */
    $scope.inputLocked = function() {
        return ($scope.data.conceptSelected | $scope.creatingConcept);
    }

    /**
      * Open the concept creation form.
      */
    $scope.startCreatingConcept = function() {
        if ($scope.assertUnique) {
            $scope.creatingConcept = true;

            Type.list().$promise.then(function(data) {
                $scope.conceptTypes = data.results;
            })
        } else {
            $scope.creatingConcept = false;
        }
    }

    /**
      *  In order to create a new Concept, the user must not have already
      *   selected a Concept and must have entered at least three characters
      *   for the new Concept label.
      */
    $scope.canCreateConcept = function() {
        return (!$scope.conceptSelected() & $scope.query.length > 2)
    }

    /**
      *  A new Concept can be created once the user has entered a description
      *   and selected a Type.
      */
    $scope.readyToCreateConcept = function() {
        return ($scope.newConcept.typed != null & $scope.newConcept.description != null);
    }

    /**
      * Assuming that the user has entered data for a new Concept, this method
      *  should submit those data to create a new Concept and then trigger
      *  appellation creation (provided to the current scope by the
      *  AppellationController).
      *
      * Setting `uri` to 'generate' tells the Concept endpoint that this is a
      *  brand new concept.
      */
    $scope.createConceptAndAppellation = function() {
        var data = {
            uri: 'generate',
            label: $scope.query,
            authority: 'VogonWeb',
            typed: $scope.newConcept.typed.id,
            description: $scope.newConcept.description,
            pos: 'noun',
        }
        var concept = new Concept(data);

        concept.$save().then(function(c) {
            $scope.data.selectedConcept = c;
            $scope.createAppellation();
        });

    }

    $scope.reset();

    $(document).keydown(function(event) {
        if(event.which == 27) {     // ESC key.
            $scope.reset();
        }
    });

    // Listen for the parent to reset.
    $scope.$on('reset', function (event, data) {
        $scope.reset();
    });

    $scope.$on('newAppellation', function(e, d) {
        $scope.creatingConcept = false;
        $scope.assertUnique = false;
    });
}]);
