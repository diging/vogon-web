/**
  * Since we need to keep track of Appellations in several different places in
  *  the application, we use the appellationService as a clearing-house for
  *  Appellations.
  */

angular.module('annotationApp').factory('appellationService',
               ['$rootScope', '$q', 'Appellation',
                function($rootScope, $q, Appellation) {
    return {
        appellations: [],    // Holds all currently loaded Appellations.
        appellationHash: {}, // Indexes Appellations by their interpretation.
        appellationsById: {}, // Indexes Appellations by ID.
        regions: {},    // Indexes regionDvis by appellation ID.
        taggedRegions: {},

        /**
          * Add appellation ID and class to appellated words.
          */
        tagWordAsAppellation: function(appellation) {
            // Could be here.
            var tokenIds = appellation.tokenIds.split(',');
            if (tokenIds.length > 0 & MODE == 'text') {
                tokenIds.forEach(function(tokenId) {
                    // Hovering over an appellation displays a tooltip that shows
                    //  the label and type of the interpretation (concept).
                    $('word#' + tokenId).attr('appellation', appellation.id)
                        .attr('data-toggle', 'tooltip')
                        .addClass('appellation')
                        .tooltip({
                            container: 'body',
                            title: appellation.interpretation_label + ' (' + appellation.interpretation_type_label + ')'
                        });  // Fix jumpiness.
                });
            } else if (MODE == 'image') {

            }
        },

        tagRegionAsAppellation: function(appellation) {
            if (appellation.id in this.taggedRegions) return;

            var $elem = $('#digilib-image-container');
            var data = $elem.data('digilib');

            var rect = parseCoords(data, appellation.position.position_value);


            var attr = {'class': 'vogonRegionURL vogonOverlay dl-region appellation', 'appellation': appellation.id};
            var item = { 'rect': rect, 'attributes': attr };
            var $regionDiv = addRegionDiv(data, item);
            $(data).trigger('newRegion', [$regionDiv]);
            this.taggedRegions[appellation.id] = appellation;
        },

        indexRegion: function(appellation, region) {
            this.regions[appellation.id] = region;
        },

        /**
          * Add Appellations retrieved from the REST interface to this service.
          */
        insertAppellations: function(appellations) {
            var service = this;
            this.appellations = appellations;
            this.appellations.forEach(function(appellation) {
                service.indexAppellation(appellation);
                if (appellation.position) {
                    if (appellation.position.position_type == 'TI' && MODE == 'text') service.tagWordAsAppellation(appellation);
                    if (appellation.position.position_type == 'BB' && MODE == 'image') service.tagRegionAsAppellation(appellation);
                };
            });

            // Used only when annotating an image.
            if (typeof packRegions != 'undefined') {
                var $elem = $('#digilib-image-container');
                var data = $elem.data('digilib');
                packRegions(data);
                renderRegions(data);
                $elem.digilib.apply($elem, ['redisplay', data]);
            }
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

            if (appIndex > -1) this.appellations.splice(appIndex, 1)
            // Remove from ID index.
            if (appId in this.appellationsById) {
                delete this.appellationsById[appId];
            }

            if (appId in this.taggedRegions) {
                delete this.taggedRegions[appId];
            }
        },

        /**
          * Retrieves all Appellations for the current text from the REST
          *  interface.
          */
        getAppellations: function(callback) {
            var service = this;
            return Appellation.query().$promise
                .then(function(data) {
                    service.insertAppellations(data.results);
                })
                .finally(function(data) {
                    callback(service.appellations);
                });
        },

        /**
          * Retrieve the promise of an Appellation by ID.
          */
        getAppellation: function(appId) {
            // First check our current index.
            var service = this;
            if (appId in this.appellationsById) {
                return $q(function(resolve, reject) {
                    resolve(service.appellationsById[appId]);
                });
                // We use the $q service to mimic the Resource get promise in
                //  the else case.
                // var deferred = $q.defer();
                // deferred.resolve();
                // return deferred.promise;
            } else {
                return Appellation.get({id: appId}).$promise;
            }
        },

        /**
          * Get the position index of an Appellation (by ID) in the service.
          */
        getAppellationIndex: function(appId) {  // Retrieve by ID.
            var foundIndex = null;
            this.appellations.forEach(function(appellation, index) {
                if (String(appellation.id) == String(appId)) foundIndex = index;
            });
            return foundIndex;
        },


        /**
          * Create and index a new Appellation.
          */
        createAppellation: function(data) {
            var appellation = new Appellation(data);
            var service = this;

            return appellation.$save().then(function(a, rHeaders) {
                service.appellations.push(a);
                if(service.appellationHash[a.interpretation] == undefined) {
                    service.appellationHash[a.interpretation] = [];
                }
                service.appellationHash[a.interpretation].push(a);

                service.tagWordAsAppellation(a);
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
