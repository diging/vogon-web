/**
  * Since we need to keep track of Appellations in several different places in
  *  the application, we use the appellationService as a clearing-house for
  *  Appellations.
  */

angular.module('annotationApp').factory('appellationService', ['$rootScope', '$q', 'Appellation', function($rootScope, $q, Appellation) {
    return {
        appellations: [],    // Holds all currently loaded Appellations.
        appellationHash: {}, // Indexes Appellations by their interpretation.
        appellationsById: {}, // Indexes Appellations by ID.

        /**
          * Add Appellations retrieved from the REST interface to this service.
          */
        insertAppellations: function(appellations) {
            var service = this;
            this.appellations = appellations;
            this.appellations.forEach(function(appellation) {
                service.indexAppellation(appellation);
            });
        },

        /**
          * Index a single Appellation.
          */
        indexAppellation: function(appellation) {
            if(this.appellationHash[appellation.interpretation] == undefined) {
                this.appellationHash[appellation.interpretation] = [];
            }
            this.appellationHash[appellation.interpretation].push(appellation);
            this.appellationsById[appellation.id] = appellation;
        },

        /**
          * Clears an Appellation from the service. Does NOT delete the
          *  Appellation via the REST interface.
          */
        removeAppellation: function(appId) {
            if (!(appId in this.appellationsById)) return; // Nothing to do.

            var appIndex = this.getAppellationIndex(appId);
            var appellation = this.appellationsById[appId];
            var foundIndex = null;

            // Remove from interpretation index.
            if (appellation.interpretation in this.appellationHash) {
                this.appellationHash[appellation.interpretation].forEach(function(appellation, index) {
                    if (String(appellation.id) == String(appId)) foundIndex = index;
                });
                if (foundIndex != null) this.appellationHash[appellation.interpretation].splice(foundIndex, 1);
            }

            if (appIndex > -1) this.appellations.slice(appIndex, 1)

            // Remove from ID index.
            if (appId in this.appellationsById) {
                delete this.appellationsById[appId];
            }
        },

        /**
          * Retrieves all Appellations for the current text from the REST
          *  interface.
          */
        getAppellations: function(callback) {
            return Appellation.query().$promise
                .then(this.insertAppellations)
                .finally(callback);
        },

        /**
          * Retrieve the promise of an Appellation by ID.
          */
        getAppellation: function(appId) {
            // First check our current index.
            if (appId in this.appellationsById) {
                // We use the $q service to mimic the Resource get promise in
                //  the else case.
                var deferred = $q.defer();
                deferred.resolve(this.appellationsById[appId]);
                return deferred.promise;
            } else {
                return Appellation.get({id: appId}).$promise;
            }
        },

        /**
          * Get the position index of an Appellation (by ID) in the service.
          */
        getAppellationIndex: function(appId) {  // Retrieve by ID.
            var foundIndex = null;
            service.appellations.forEach(function(appellation, index) {
                if (String(appellation.id) == String(appId)) foundIndex = index;
            });
            return foundIndex;
        },


        createAppellation: function(data) {
            var appellation = new Appellation(data);
            var service = this;

            return appellation.$save().then(function(a, rHeaders) {
                service.appellations.push(a);
                if(service.appellationHash[a.interpretation] == undefined) {
                    service.appellationHash[a.interpretation] = [];
                }
                service.appellationHash[a.interpretation].push(a);
                $rootScope.$broadcast('newAppellation', a);
                return a;
            });
        },

        /**
          * Completely delete an Appellation.
          */
        deleteAppellation: function(appId) {
            var service = this;
            this.getAppellation(appId).then(function(appellation) {
                // Ask the user to confirm deletion (via modal).
                angular.element($('#deleteAppellationModal')).scope()
                    .open({appellation: appellation}, function() {
                        // Perform the deletion.
                        Appellation.delete({id: appId}).$promise.then(function(){
                            $rootScope.$broadcast('deleteAppellation', appellation);
                        });
                        service.removeAppellation(appId);
                    });

            });
        },
    }
}]);
