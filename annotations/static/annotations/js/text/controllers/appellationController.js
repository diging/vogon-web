angular.module('annotationApp')
    .controller('AppellationsController',
        ['$scope', '$rootScope', 'appellationService', 'selectionService',
         function($scope, $rootScope, appellationService, selectionService) {

    $scope.appellations = [];
    appellationService.getAppellations(function(data) {
        $scope.appellations = data;
    });

    selectionService.expectWords(function(data) {
        
    });
}]);
