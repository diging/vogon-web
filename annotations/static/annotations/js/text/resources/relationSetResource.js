/**
  * Each Concept has a specific Type, usually from the CIDOC-CRM.
  */
angular.module('annotationApp').factory('RelationSet', function($resource) {
    return $resource('/rest/relationset/:id/', {
        text: TEXTID,
        thisuser: true
    }, {
        list: {
            method: 'GET',
            isArray: false,
            headers: {'Content-Type': 'application/json'}
        },
        query: {
            method: 'GET',
            isArray: false,
            headers: {'Content-Type': 'application/json'}

        },
        save: {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        }
    });
});
