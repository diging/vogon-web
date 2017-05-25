angular.module('annotationApp').controller('ActionPanelController', ['$scope', '$rootScope', function($scope, $rootScope) {

    $scope.reset = function() {
        console.log('reset::  ActionPanelController');
        $scope.deregister_appellationTab = $scope.$on('appellationTab', function() {
            console.log('received appellationTab event');
            $('#appellationTabAnchor').click();
        });

        $scope.deregister_relationTab = $scope.$on('relationTab', function() {
            $('#relationTabAnchor').click();

        });
        $(document).unbind("keydown", $scope.handle_keydown);
        $(document).keydown($scope.handle_keydown);
    }

    $scope.handle_keydown = function(event) {
        if (event.which == 27) {
            $scope.deregister_appellationTab();
            $scope.deregister_relationTab();
            $scope.reset();
        }
    }

    $scope.startCreatingRelation = function() {
        $('#relationTabAnchor').click();
        $scope.$broadcast('startCreatingRelation');
    }

    $scope.reset();

}]);
