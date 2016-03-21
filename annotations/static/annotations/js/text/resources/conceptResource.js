/**
  * Concepts are used to create Appellations.
  */
angular.module('annotationApp').factory('Concept', function($resource) {
    return $resource('/rest/concept/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
            isArray: false,
        }
    });
});
