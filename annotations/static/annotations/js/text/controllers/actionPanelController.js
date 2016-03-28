angular.module('annotationApp').controller('ActionPanelController', ['$scope', '$rootScope', function($scope, $rootScope) {


    $scope.$on('appellationTab', function() {
        $('#appellationTabAnchor').click();
    });

    $scope.$on('relationTab', function() {
        $('#relationTabAnchor').click();

    });

    $scope.startCreatingRelation = function() {
        $('#relationTabAnchor').click();
        $scope.$broadcast('startCreatingRelation');
    }

}]);
