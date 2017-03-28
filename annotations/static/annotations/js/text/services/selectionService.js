angular.module('annotationApp').factory('selectionService', ['appellationService', function(appellationService) {
    var service = {
        // Word callback hoppers.
        word_success_callbacks: [],
        word_failure_callbacks: [],

        // Region callback hoppers.
        region_success_callbacks: [],
        region_failure_callbacks: [],

        // Appellation callback hoppers.
        appellation_success_callbacks: [],
        appellation_failure_callbacks: [],

        // Current selection. Holds {jQuery} objects.
        selected_words: $(),
        selected_regions: null,
        selected_appellation: null,

        deferred: {
            word_success_callbacks: [],
            word_failure_callbacks: [],
            region_success_callbacks: [],
            region_failure_callbacks: [],
            appellation_success_callbacks: [],
            appellation_failure_callbacks: [],
        },

        skipAppellationPopover: false,
        skipWordPopover: false,
        skipRegionPopover: false,
        persistHighlighting: false,
    }

    /**
      * Put existing expectations on hold.
      */
    service.defer = function() {
        service.deferred.word_success_callbacks = service.word_success_callbacks;
        service.deferred.word_failure_callbacks = service.word_failure_callbacks;
        service.deferred.appellation_success_callbacks = service.appellation_success_callbacks;
        service.deferred.appellation_failure_callbacks = service.appellation_failure_callbacks;
        service.deferred.region_success_callbacks = service.region_success_callbacks;
        service.deferred.region_failure_callbacks = service.region_failure_callbacks;

        service.word_success_callbacks = [];
        service.word_failure_callbacks = [];
        service.appellation_success_callbacks = [];
        service.appellation_failure_callbacks = [];
        service.region_success_callbacks = [];
        service.region_failure_callbacks = [];
    }

    /**
      * Re-instate deferred expectations.
      */
    service.resume = function() {
        service.word_success_callbacks = service.deferred.word_success_callbacks;
        service.word_failure_callbacks = service.deferred.word_failure_callbacks;
        service.appellation_success_callbacks = service.deferred.appellation_success_callbacks;
        service.appellation_failure_callbacks = service.deferred.appellation_failure_callbacks;

        service.region_success_callbacks = service.deferred.region_success_callbacks;
        service.region_failure_callbacks = service.deferred.region_failure_callbacks;

        service.deferred = {
            word_success_callbacks: [],
            word_failure_callbacks: [],
            appellation_success_callbacks: [],
            appellation_failure_callbacks: [],
            region_success_callbacks: [],
            region_failure_callbacks: [],
        }
    }

    /**
      * Indicates whether/not we are now in the process of selecting words.
      */
    service.wordsAreSelected = function() {
        return (service.selected_words.length > 0);
    }

    /**
      * Unselect all words.
      */
    service.resetWordSelection = function() {
        service.selected_words.removeClass("selected");
        $($('.popover').attr('parent')).popover('destroy');
        service.selected_words = $();
    }

    /**
      * Unselect all regions.
      */
    service.resetRegionSelection = function() {

    //   service.selected_regions.removeClass("selected");
        $($('.popover').attr('parent')).popover('destroy');
        service.selected_regions = null;
        $('.selected').removeClass("selected");

    }

    service.removeNonCommittedRegions = function() {
        $('div.dl-region').each(function(i, elem) {
            if ($(elem).attr('appellation') == undefined) {
                $(elem).remove();
            }
        });
    }

    service.startSelectingRegion = function(evt) {
        evt.stopPropagation();
        service.removeNonCommittedRegions();

        var $elem = $('#digilib-image-container');
        var data = $elem.data('digilib');

        var onComplete = function (data, rect) {
            if (rect == null) return;

            // // Signal to the rest of the app that a region is selected.
            var count = getRegions(data, 'regionURL').length;
            var attr = {'class': 'vogonRegionURL vogonOverlay dl-region notcommitted'};
            var item = {'rect': rect, 'index': count, 'attributes': attr};
            var $regionDiv = addRegionDiv(data, item);

            // $('body').trigger('regionSelected', [packCoords($regionDiv.data().rect)]);

            $(data).trigger('newRegion', [$regionDiv]);
            packRegions(data);
            renderRegions(data);
            $elem.digilib.apply($elem, ['redisplay', data]);
            service.handleRegion(null, packCoords($regionDiv.data().rect), $regionDiv);
        };
        $elem.digilib.apply($elem, ['defineArea', onComplete, 'BOBregionArea']);
    };

    /**
      * Unselect all appellations.
      *
      * This is kind of weird at the moment, since we only select one
      *  appellation at a time.
      */
    service.resetAppellationSelection = function() {
        if (!service.persistHighlighting) {
            service.unhighlightAppellations();
        }
        $($('.popover').attr('parent')).popover('destroy');
        service.selected_appellation = null;
    }

    /**
      *  Clear word callback hoppers.
      */
    service.resetWordCallbacks = function() {
        service.word_success_callbacks = [];
        service.word_failure_callbacks = [];
    }

    /**
      *  Clear region callback hoppers.
      */
    service.resetRegionCallbacks = function() {
        service.region_success_callbacks = [];
        service.region_failure_callbacks = [];
    }

    /**
      *  Clear appellation callback hoppers.
      */
    service.resetAppellationCallbacks = function() {
        service.appellation_success_callbacks = [];
        service.appellation_failure_callbacks = [];
    }

    /**
      *  Handle the failure to select a word.
      */
    service.failWordExpectation = function() {
        service.word_failure_callbacks.forEach(function(expectation) {
            expectation.callback();
        });
        service.resetWordCallbacks();
        service.resetWordSelection();
    }

    /**
      *  Handle successful word selection.
      */
    service.succeedWordExpectation = function() {
        var remainder = [];
        service.word_success_callbacks.forEach(function(expectation) {
            expectation.callback(service.selected_words);
            if (expectation.autorelease) {
                // pass
            } else {
                remainder.push(expectation);
            }
        });
        service.word_success_callbacks = remainder;

    }

    /**
      *  Handle the failure to select a word.
      */
    service.failRegionExpectation = function() {

        service.region_failure_callbacks.forEach(function(expectation) {
            expectation.callback();
        });
        service.resetRegionCallbacks();
        service.resetRegionSelection();
    }

    /**
      *  Handle successful region selection.
      */
    service.succeedRegionExpectation = function() {

        var remainder = [];
        service.region_success_callbacks.forEach(function(expectation) {
            expectation.callback(service.selected_regions);
            if (expectation.autorelease) {
                // pass
            } else {
                remainder.push(expectation);
            }
        });
        service.region_success_callbacks = remainder;
    }



    /**
      *  Handle the failure to select an appellation.
      */
    service.failAppellationExpectation = function() {
        service.appellation_failure_callbacks.forEach(function(expectation) {
            expectation.callback();
        });
        service.resetAppellationCallbacks();
        service.resetAppellationSelection();
    }

    /**
      *  Handle successful appellation selection.
      */
    service.succeedAppellationExpectation = function() {
        var remainder = [];
        service.appellation_success_callbacks.forEach(function(expectation) {
            expectation.callback(service.selected_appellation);
            if (expectation.autorelease) {
                // pass
            } else {
                remainder.push(expectation);
            }
        });
        service.appellation_success_callbacks = remainder;
    }

    /**
      *  Discriminates between words that are and are not part of appellations.
      *  @param {jQuery} word - A jQuery-selected <word> object.
      */
    service.isAppellation = function(word) {
        if (word.is('.appellation')) return true;
        return false;
    }

    /**
      *  Retrieves the appellation ID from a jQuery-selected <word> element.
      *  @param {jQuery} word - A jQuery-selected <word> object.
      */
    service.getAppellationID = function(word) {
        if (service.isAppellation) return word.attr('appellation');
    }

    /**
      *  Register success and failure callbacks for word selection events.
      *  @param {function} success_callback - Function to be called when the user selects a word.
      *  @param {function} failure_callback - Function to be called when the user fails to select a word.
      *  @param {bool} autorelease - If false, word selection will not be released until service.releaseWords() is called.
      */
    service.expectWords = function(success_callback, failure_callback, autorelease) {
        if (success_callback) service.word_success_callbacks.push({
            'callback': success_callback,
            'autorelease': autorelease,
        });
        if (failure_callback) service.word_failure_callbacks.push({
            'callback': failure_callback,
            'autorelease': autorelease,
        });
    }

    /**
      *  Register success and failure callbacks for region selection events.
      *  @param {function} success_callback - Function to be called when the user selects a region.
      *  @param {function} failure_callback - Function to be called when the user fails to select a region.
      *  @param {bool} autorelease - If false, region selection will not be released until service.releaseRegions() is called.
      */
    service.expectRegion = function(success_callback, failure_callback, autorelease) {

        if (success_callback) service.region_success_callbacks.push({
            'callback': success_callback,
            'autorelease': autorelease,
        });
        if (failure_callback) service.region_failure_callbacks.push({
            'callback': failure_callback,
            'autorelease': autorelease,
        });

    }

    service.releaseRegions = function() {
        service.resetRegionSelection();
        service.resetRegionCallbacks();
    }

    service.releaseWords = function() {
        service.resetWordSelection();
        service.resetWordCallbacks();
    }

    service.releaseAppellations = function() {
        service.resetAppellationCallbacks();
        service.resetAppellationSelection();
    }

    /**
      *  Register success and failure callbacks for appellation selection events.
      *  @param {function} success_callback - Function to be called when the user selects an appellation.
      *  @param {function} failure_callback - Function to be called when the user fails to select an appellation.
      */
    service.expectAppellation = function(success_callback, failure_callback, autorelease) {
        if (success_callback) service.appellation_success_callbacks.push({
            'callback': success_callback,
            'autorelease': autorelease,
        });
        if (failure_callback) service.appellation_failure_callbacks.push({
            'callback': failure_callback,
            'autorelease': autorelease,
        });
    }

    /**
      * Callback for DigiLib region selection event.
      * @param {jQuery.Event} event - Click event with a valid ``target``.
      * @param {Object} data - DigiLib data object.
      * @param {Object} rect - DigiLib rect object.
      */
    service.handleRegion = function(event, coords, regionDiv) {
        service.replaceRegionSelection({
            'coords': coords,
            'regionDiv': regionDiv,
        });

        service.succeedRegionExpectation();
    }

    /**
      *  Callback for <word> click event.
      *  @param {jQuery.Event} event - Click event with a valid ``target``.
      */
    service.handleClick = function(event) {
        if (event.target.localName != 'word' && event.target.localName != 'div') return;
        event.stopPropagation();

        var word = $(event.target);
        // If the word is part of an appellation, select it.
        if (service.isAppellation(word)) {
            // service.handleSelectAppellation(event);
            service.replaceAppellationSelection(word);

        // If the word is not part of an Appellation, add word to the word
        //  selection hopper.
        } else {
            if (service.selected_words.length > 0 & event.shiftKey) {
                // $.add() does not modify in-place.
                service.extendWordSelection(word);
                // service.selected_words = service.selected_words.add(word);
            } else {
                service.replaceWordSelection(word);
            }
            service.selected_words.addClass("selected");
            service.selectedWordPopover();
        }
    }

    service.replaceWordSelection = function(word) {
        service.resetWordSelection();
        service.selected_words = word;
    }

    service.replaceRegionSelection = function(region) {

        service.resetRegionSelection();
        service.selected_regions = region;
    }

    service.unhighlightAppellations = function() {
        $('.appellation').removeClass('selected');
    }

    service.highlightAppellation = function(appellation) {
        var elem = $('[appellation=' + appellation.id + ']');
        elem.addClass('selected');
    }

    service.scrollToAppellation = function(elem) {
        var pos = elem.position();
        if (pos) {
            $('.action-body').animate({ scrollTop: pos.top}, 500);
        }
    }

    service.replaceAppellationSelectionDirect = function(appellation) {
        service.resetAppellationSelection();
        service.selected_appellation = appellation;
        service.highlightAppellation(appellation);
        if (service.skipAppellationPopover) {
            // Appellation is selected as soon as the user clicks it.
            service.succeedAppellationExpectation();
        } else {
            // Require user input (e.g. click a button) to complete the
            //  selection.
            // service.selectedAppellationPopover();

        }
    }

    /**
      * Clear the existing Appellation selection, and replace it with the
      *  Appellation associated with ``word``.
      */
    service.replaceAppellationSelection = function(word) {
        service.resetAppellationSelection();
        appellationService.getAppellation(service.getAppellationID(word)).then(service.replaceAppellationSelectionDirect);

    }


    /**
      * Display a popover with button on the last selected word.
      */
    service.selectedWordPopover = function() {
        var lastId = service.selected_words[service.selected_words.length - 1].id;
        $($('.popover').attr('parent')).popover('destroy');
        if (lastId) {
            $('word#' + lastId).popover({
                html: true,
                template: '<div class="popover" parent="word#' + lastId + '" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content popover-action"></div></div>',
                content:'<a class="btn btn-xs glyphicon glyphicon-tag word-popover-button"></a>',
                container: 'body'   // Prevents shifting text.
            });
            $('word#' + lastId).popover('show');
        }
    }

    /**
      * Display a popover with button on the selected region.
      */
    service.selectedRegionPopover = function() {
        $($('.popover').attr('parent')).popover('destroy');
        var selectedRegionElem = service.selected_regions.elem;
        $(service.selected_regions.elem).popover({
            html: true,
            template: '<div class="popover" parent="#' + selectedRegionElem[0].id + '" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content popover-action"></div></div>',
            content:'<a class="btn btn-xs glyphicon glyphicon-tag region-popover-button"></a>',

        });
        $(service.selected_regions.elem).popover('show');
    }

    /**
      * Display a popover with button on the last selected word.
      */
    service.selectedAppellationPopover = function() {
        var selector = $('word[appellation=' + service.selected_appellation.id + ']');
        $($('.popover').attr('parent')).popover('destroy');
        selector.last().popover({
            html: true,
            template: '<div class="popover" parent="word[appellation=' + service.selected_appellation.id + ']" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content popover-action"></div></div>',
            content:'<a class="btn btn-xs glyphicon glyphicon-plus appellation-popover-button"></a>',
            container: 'body'   // Prevents shifting text.
        });
        selector.last().popover('show');
    }

    /**
      *  Callback for select word event.
      *  @param {jQuery.Event} event
      */
    service.handleSelectWord = function(event) {
        service.succeedWordExpectation();
    }

    /**
      *  Callback for select region event.
      *  @param {jQuery.Event} event
      */
    service.handleSelectRegion = function(event) {

        service.succeedRegionExpectation();
    }

    /**
      *  Callback for select appellation event.
      *  @param {jQuery.Event} event
      */
    service.handleSelectAppellation = function(event) {
        service.succeedAppellationExpectation();
    }

    /**
      * Handles the event that user presses the enter key on their keyboard.
      */
    service.handleEnter = function(event) {
        if (service.wordsAreSelected()) service.handleSelectWord(event);
    }

    /**
      *  Callback for ESC key event.
      */
    service.handleEsc = function(event) {
        service.releaseWords();
        service.unhighlightAppellations();
        service.removeNonCommittedRegions();
        $($('.popover').attr('parent')).popover('destroy');
    }

    /**
      * Select all elements from start through end.
      * @param {jQuery} start - The starting element.
      * @param {jQuery} end - The ending element.
      */
    service.selectIntermediateWords = function(start, end) {
        // Select words between start and end. If start, end, or any
        // intermediate words are appellations, abort and clear all selections.
        var toSelect = start.nextUntil(end, "word").add(start).add(end);

        if (toSelect.is('.appellation')) {
            // Selection crosses an appellation. Abort!
            return false;
        }

        // Otherwise, select everything.
        service.selected_words = service.selected_words.add(toSelect);
        return true;
    }

    /**
      * Extend the current selection of words to the target word, including all intermediate words.
      * @param {jQuery} target - The word element to which the current selection should be extended.
      */
    service.extendWordSelection = function(target) {
        // User can select multiple non-appellation words by holding
        //  the shift key.
        var first = service.selected_words.first();
        var last = service.selected_words.last();
        var index_target = $('word').index(target);
        var index_first = $('word').index(first);
        var index_last = $('word').index(last);
        var inter;

        // Select words between the new target word and either the
        //  start or end of the current selection.
        if (index_target < index_first) {       // Target is earlier.
            inter = service.selectIntermediateWords(target, first);
            targetElement = last;
        } else if (index_last < index_target) {     // Target is later.
            inter = service.selectIntermediateWords(last, target);
            targetElement = target;
        }

        // If multi-selection was aborted, the `targetElement` (where the icons)
        //  should appear should be the last element clicked (`target`).
        if (!inter){
            service.replaceWordSelection(target);
        }
    }

    service.bindWords = function() {
        $('a').click(service.defineUserRegion);
        $('body').unbind("click");
        $('body').on('click', '#image-select-region', service.startSelectingRegion);
        $('body').on('click', service.handleClick);

        // A region has been selected in the jquery.digilib.vogon plugin.
        // $('body').on('regionSelected', service.handleRegion);


        service.persistHighlighting = false;

        $('body').on('click', '.word-popover-button', function() {
            $($('.popover').attr('parent')).popover('destroy');
            service.handleSelectWord();
        });

        $('body').on('click', '.region-popover-button', function() {
            $($('.popover').attr('parent')).popover('destroy');
            service.handleSelectRegion();
        });

        $('body').on('click', '.appellation-popover-button', function() {
            $($('.popover').attr('parent')).popover('destroy');
            service.handleSelectAppellation();
        });

        $(document).unbind('keydown', service.handleKeydown);
        $(document).keydown(service.handleKeydown);

    }
    service.handleKeydown = function(event) {
        if(event.which == 13) service.handleEnter(event);
        if(event.which == 27) service.handleEsc(event);
    }

    service.bindWords();

    // $(document).keydown(function(event) {
    //     if(event.which == 27) {     // ESC key.
    //         service.resetAppellationSelection();
    //         service.resetWordSelection();
    //         service.resetRegionSelection();
    //         service.bindWords();
    //     }
    // });
    return service;
}]);
