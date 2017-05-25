/**
  * Each Concept has a specific Type, usually from the CIDOC-CRM.
  */
angular.module('annotationApp').factory('Type', function($resource) {
    return $resource(BASE_URL + '/rest/type/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
        }
    });
});
