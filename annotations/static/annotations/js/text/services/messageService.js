/**
  * The messageService handles view-wide messages to the user. For example,
  *  instructions about the next step in a process.
  */
angular.module('annotationApp').factory('messageService', function($rootScope) {
    var service = {}

    /**
      * Sets the current message.
      */
    service.newMessage = function(message, type) {
        var alertScope = angular.element($('#alerts')).scope();
        alertScope.closeAlert(0);
        alertScope.addAlert(message, type);
        return;
        // $rootScope.$broadcast('newMessage', message);
    }

    /**
      * Clears the current message, and displays the default message if
      *  one is available.
      */
    service.reset = function() {
        var alertScope = angular.element($('#alerts')).scope();
        alertScope.defaultAlert();
        if(!alertScope.$$phase) alertScope.$apply();
        return;
    }
    return service;
});
