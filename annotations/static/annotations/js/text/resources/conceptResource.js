/**
  * Concepts are used to create Appellations.
  */
angular.module('annotationApp').factory('Concept', function($resource) {
    return $resource('/rest/concept/:id/', {}, {
        list: {
            method: 'GET',
            isArray: false,
        },
        query: {
            method: 'GET',
            isArray: false,
        },
        save: {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        }
    });
});
