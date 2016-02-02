angular.module('annotationApp')
    .controller('AppellationsController',
        ['$scope', '$rootScope', 'appellationService', 'selectionService', 
         'conceptService', 'Appellation',
         function($scope, $rootScope, appellationService,  selectionService,
                  conceptService, Appellation) {

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
