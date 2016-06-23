angular.module('annotationApp')
    .controller('AppellationsController',
        ['$scope', '$rootScope', 'appellationService', 'selectionService',
         function($scope, $rootScope, appellationService, selectionService) {

    $scope.data = {};    // Child controllers should update this object.

    appellationService.getAppellations(function(data) {
        $scope.appellations = data;
    });

    /**
      *  Generate a string representation of the selected passage (for
      *   Concept.stringRep field).
      */
    var getStringRep = function(selector, delim) {
        var stringRep = $.map(selector, function(selem) {
            return selem.innerHTML;
        });
        return stringRep.join(delim);
    }

    /**
      *  Stitch word IDs together into a string suitable for Concept.tokenIds.
      */
    var getTokenIds = function(selector) {
        var tokenIds = [];
        selector.each(function () { tokenIds.push(this.id); });
        return tokenIds.join(',');
    }

    /**
      *  Indicates whether or not a concept is currently selected.
      */
    $scope.conceptSelected = function() {
        return ($scope.data.selectedConcept != null);
    }

    /**
      *  Create a new Appellation (via AppellationService) using the selected
      *   words and concept.
      */
    $scope.createAppellation = function() {
        var data = {
            "tokenIds": getTokenIds($scope.selectedWords),
            "stringRep": getStringRep($scope.selectedWords, ' '),
            "startPos": null,
            "endPos": null,
            "asPredicate": false,
            "occursIn": TEXTID,
            "createdBy": USERID,
            "interpretation": $scope.data.selectedConcept.id,
        }

        appellationService.createAppellation(data).then(function(appellation) {
            $scope.selectAppellation(appellation);
            $scope.$emit('appellationCreated');
            reloadGraph();  // Wait until the appellation is actually created.
            $scope.reset();
        });

    }

    $scope.reset = function() {
        $scope.appellations = [];
        $scope.data.selectedConcept = null;
        $scope.hideAppellationCreate = true;
        $scope.hideCreateConcept = true;
        $scope.hideCreateConceptDetails = true;

        if (MODE == 'text') {
            // Listen for the user to select a word.
            selectionService.expectWords(function(data) {
                $scope.hideAppellationCreate = false;
                $scope.selectedWords = data;
                $scope.selectedText = getStringRep(data, ' ');
                $scope.$emit('appellationTab');
                $scope.$apply();

            });
        }

        if (MODE == 'image') {
            selectionService.expectRegion(function(data) {

                $scope.hideAppellationCreate = false;
                $scope.selectedRegions = data;
                $scope.selectedImage = null;

                var cparts = data.coords.split(',');
                console.log(data.coords);
                var wx = cparts[0],
                    wy = cparts[1],
                    ww = cparts[2],
                    wh = cparts[3];

                $('#digilib-selection-container').empty();
                $('#digilib-selection-container').append('<div id="digilib-selection-preview" style="position: relative;"><img src="" /></div>');
                var previewWidth = $('#tabAppellations').width();
                var imageLocation = 'http://diging.asu.edu:8080/digilib/servlet/Scaler?dw='+previewWidth+'&fn=testImage&wx='+wx+'&wy='+wy+'&ww='+ww+'&wh='+wh;
                console.log(imageLocation);
                $('#digilib-selection-preview img').attr('src', imageLocation);
                $('#digilib-selection-preview').digilib({
                    interactionMode: 'embedded',
                    digilibBaseUrl: '/static/annotations/js/digilib',
                    buttonSettings : {
                        'embedded': {
                            'imagePath': '',
                            'buttonSetWidth': 0,
                            'buttonSets': [],
                            'standardSet': [],
                            'specialSet': [],
                            'pageSet': [],
                        }
                    },
                });
                $scope.$emit('appellationTab');
                $scope.$apply();
            });
        }

        // Re-populate the list of existing Appellations.
        appellationService.getAppellations(function(appellations) {
            $scope.appellations = appellations;
        });

        selectionService.releaseWords();

        // Make sure that all of the children know.
        $scope.$broadcast('reset');
    }

    /**
      *  Trigger Appellation selection service via click event.
      */
    $scope.selectAppellation = function(appellation) {

        console.log('selectAppellation: ' + appellation.id);

        // Select the last word.
        var tokenIds = appellation.tokenIds.split(',');
        var elem = $('word#' + tokenIds[tokenIds.length - 1]);

        // Scroll to the word (leave an offset at the top).
        $('html, body').animate({ scrollTop: elem.offset().top - 20,}, 500);

        // Then click!
        elem.trigger('click');
    }

    $scope.reset();

    $(document).keydown(function(event) {
        if(event.which == 27) {     // ESC key.
            $scope.reset();
        }
    });

}]);
