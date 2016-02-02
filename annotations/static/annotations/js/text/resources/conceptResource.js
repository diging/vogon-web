/**
  * Concepts are used to create Appellations.
  */
angular.module('annotationApp').factory('Concept', function($resource) {
    return $resource(BASELOCATION + '/rest/concept/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
        }
    });
});
