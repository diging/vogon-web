/**
  * Concepts are used to create Appellations.
  */

angular.module('annotationApp').factory('Concept', function($resource) {
    return $resource(BASE_URL + '/rest/concept/:id/', {}, {
        list: {
            method: 'GET',
            isArray: false
        },
        query: {
            method: 'GET',
            isArray: false,
            url: BASE_URL + '/rest/concept/search/'
        },
        save: {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        }
    });
});
