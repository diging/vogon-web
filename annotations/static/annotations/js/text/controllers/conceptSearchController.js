
app.controller('ConceptSearchController', ['$scope', 'Concept', function($scope, Concept) {
    $scope.concepts = [];
    $scope.query = '';
    $scope.newConcept = null;
    $scope.hideCreateConcept = true;

    $scope.search = function() {
        if ($scope.query.length > 2) {
            Concept.query({search: $scope.query, pos: 'noun', remote: true}).$promise.then(function(data){
                $scope.concepts = data;
            });
        }
    }

    $scope.select = function(concept) {
        $scope.concept = concept;
        $scope.concepts = [];
    }

    $scope.reset  = function() {
        Concept.list().$promise.then(function(data) {
            $scope.concepts = data;
        });
        $scope.concept = null;
    }

    $scope.conceptSelected = function() {
        return ($scope.concept != null);
    }

    /**
      * Open the concept creation form.
      */
    $scope.startCreatingConcept = function() {
        $scope.hideCreateConcept = false;
    }

    $scope.assertUnique = function() {
        $scope.newConcept = {};
    }

    $scope.reset();
}]);
