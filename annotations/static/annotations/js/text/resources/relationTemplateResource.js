angular.module('annotationApp').factory('RelationTemplate', function($resource) {
    return $resource('/relationtemplate/:id/', {
        format: 'json',
    }, {
        list: {
            method: 'GET',
            cache: true,
            headers: {'Content-Type': 'application/json'}
        },
        query: {
            isArray: false,
        }

    });
});