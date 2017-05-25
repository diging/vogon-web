angular.module('annotationApp')
    .controller('AppellationsController',
        ['$scope', '$rootScope', 'appellationService', 'selectionService', '$cookies',
         function($scope, $rootScope, appellationService, selectionService, $cookies) {

    $scope.data = {};    // Child controllers should update this object.

    $scope.hidden = [3,];

    $scope.isVisible = function(appellation) {
        return ($scope.hidden.indexOf(appellation.id) < 0);
    }

    $scope.hide = function(appellation) {
        $scope.hidden.push(appellation.id);
    }
    $scope.show = function(appellation) {
        $scope.hidden.splice($scope.hidden.indexOf(appellation.id), 1);
    }

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
        console.log("appellationController.createAppellation",
                    $scope.data.selectedConcept);

        if (MODE == 'text') {
            // TODO: use `position` instead of `tokenIds`.
            var identifier;
            if ($scope.data.selectedConcept.id != null) {
                identifier = $scope.data.selectedConcept.id;
            } else if ($scope.data.selectedConcept.uri) {
                identifier = $scope.data.selectedConcept.uri;
            }
            var data = {
                "tokenIds": getTokenIds($scope.selectedWords),
                "stringRep": getStringRep($scope.selectedWords, ' '),
                "project": PROJECTID,
                "startPos": null,
                "endPos": null,
                "asPredicate": false,
                "occursIn": TEXTID,
                "createdBy": USERID, // TODO: this is odd.
                "interpretation": identifier,
            };
        } else if (MODE == 'image') {
            var data = {
                "occursIn": TEXTID,
                "createdBy": USERID,
                "project": PROJECTID,
                "interpretation": $scope.data.selectedConcept.uri,
                "position": {
                    "position_type": "BB",
                    "position_value": $scope.selectedRegions.coords,
                    "occursIn": TEXTID,
                }
            };
        }

        appellationService.createAppellation(data).then(function(appellation) {

            if (data.position) {
                appellation.coords = data.position.position_value;
            }
            $scope.$emit('appellationCreated');
            reloadGraph();  // Wait until the appellation is actually created.
            $scope.reset();
            $(data.regionDiv).attr({'appellation': appellation.id});
            selectionService.bindWords();
            $(data.regionDiv).trigger('click');
            $scope.selectAppellation(appellation);
        });

    }

    $scope.reset = function() {

        $scope.appellations = [];
        $scope.data.selectedConcept = null;
        $scope.hideAppellationCreate = true;
        $scope.hideCreateConcept = true;
        $scope.hideCreateConceptDetails = true;

        selectionService.releaseWords();
        selectionService.releaseRegions();

        if (MODE == 'text') {
            // Listen for the user to select a word.
            selectionService.expectWords(function(data) {
                console.log('words!');
                $scope.hideAppellationCreate = false;
                $scope.selectedWords = data;
                $scope.selectedText = getStringRep(data, ' ');
                // $scope.$emit('appellationTab');
                $('#appellationTabAnchor').click();
                $scope.$apply();
            });
        }
        $scope.imageLocation = null;

        if (MODE == 'image') {
            // Listen for user to finish selecting a region in the main image
            //  panel.
            selectionService.expectRegion(function(data) {

                $scope.hideAppellationCreate = false;
                $scope.selectedRegions = data;
                $scope.selectedImage = null;

                var cparts = data.coords.split(',');
                var wx = cparts[0],
                    wy = cparts[1],
                    ww = cparts[2],
                    wh = cparts[3];

                $('.digilib-selection-container').empty();
                $('.digilib-selection-container').append('<div class="digilib-selection-preview" style="position: relative;"><img src="" /></div>');
                var previewWidth = $('#tabAppellations').width();
                var imageLocation = URI(IMAGE_LOCATION)
                                        .removeSearch('dw')
                                        .addSearch('wx', wx)
                                        .addSearch('wy', wy)
                                        .addSearch('ww', ww)
                                        .addSearch('wh', wh);
                if (ww > wh && previewWidth * wh/ww < 150) {
                    imageLocation.addSearch("dw", previewWidth);
                } else {
                    imageLocation.addSearch("dh", 150);
                }
                $scope.imageLocation = imageLocation.toString();
                // var imageLocation = 'http://diging.asu.edu:8080/digilib/servlet/Scaler?dw='+previewWidth+'&fn=testImage&wx='+wx+'&wy='+wy+'&ww='+ww+'&wh='+wh;
                $('.digilib-selection-preview img').attr('src', imageLocation.toString());

                $('#appellationTabAnchor').click();

                $scope.$apply();
            });
        }

        // Re-populate the list of existing Appellations.
        appellationService.getAppellations(function(appellations) {
            $scope.appellations = appellations;
        });

        // Make sure that all of the children know.
        $scope.$broadcast('reset');
    }

    $scope.scrollToAppellation = function(elem) {
        var offset = elem.offset();
        if (offset) {
            $('.appellation-list').animate({ scrollTop: offset.top - 20}, 500);
        }
    }

    $scope.scrollToWord = function(elem) {
        // Scroll to the word (leave an offset at the top).
        $('html, body').animate({ scrollTop: elem.offset().top - 20,}, 500);
    }

    /**
      *  Trigger Appellation selection service via click event.
      */
    $scope.selectAppellation = function(appellation) {

        // Select the last word.
        var tokenIds = appellation.tokenIds.split(',');
        if (tokenIds.length > 0 && MODE == 'text') {
            var elem = $('word#' + tokenIds[tokenIds.length - 1]);
            $scope.scrollToWord(elem);
            // Then click!
            elem.trigger('click');
        } else if (MODE == 'image') {

            var elem = $('[appellation="' + appellation.id + '"]');
            $scope.scrollToAppellation($('#appellation-list-item-' + appellation.id));
            // $('.vogonOverlay[appellation=' + appellation.id + ']').trigger('click');
            // elem.trigger('click');

            selectionService.replaceAppellationSelectionDirect(appellation);
            selectionService.succeedAppellationExpectation();

        };

    }

    $scope.reset();

    $scope.keydown_handler = function(event) {
        if(event.which == 27) {     // ESC key.
            $scope.reset();
        }
    }
    $(document).keydown($scope.keydown_handler);

    $scope.unbind = function() {
        $(document).unbind("keydown", $scope.keydown_handler);
    }

    $scope.$on('done', function(event) {
        $scope.unbind();
    });

    $scope.$on('relationCreated', function(event){
        $scope.reset();
    });
}]);
