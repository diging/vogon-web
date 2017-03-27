/**
  * Each Concept has a specific Type, usually from the CIDOC-CRM.
  */
angular.module(BASE_URL + 'annotationApp').factory('Type', function($resource) {
    return $resource('/rest/type/:id/', {}, {
        list: {
            method: 'GET',
            cache: true,
        }
    });
});
