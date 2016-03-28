describe('selectionService functions:', function() {


    var selectionService;

    var appellationServiceSpy = {
        getAppellation: function(id) {
            return {id: id, interpretation: 42};
        }
    }

    beforeEach(module('annotationApp'));

    beforeEach(module(function($provide) {
        $provide.value("appellationService", appellationServiceSpy);
    }));

    beforeEach(inject(function(_selectionService_, _appellationService_){
        selectionService = _selectionService_;
        appellationService = _appellationService_;
    }));

    beforeEach(function(){
        jasmine.getFixtures().fixturesPath = 'base/tests/fixtures';
          this.result = loadFixtures('textFixture.html');
    });

    describe('the isAppellation method', function() {
        it('should discriminate between words that are and are not part of an appellation.', function() {
            var word = $('<word>');
            var appellation = $('<word class="appellation">');
            expect(selectionService.isAppellation(word)).toBe(false);
            expect(selectionService.isAppellation(appellation)).toBe(true);
        });
    });

    describe('the expectWords method', function() {
        var success_callback = jasmine.createSpy('success_callback');
        var failure_callback = jasmine.createSpy('failure_callback');
        var e = {};
        it('causes a callback function to be called when the user selects a word.', function() {
            selectionService.expectWords(success_callback);
            selectionService.handleSelectWord();
            expect(success_callback).toHaveBeenCalled();
        });

        it('causes a different callback function to be called when the word selection fails.', function() {
            selectionService.expectWords(success_callback, failure_callback);
            selectionService.failWordExpectation();
            expect(failure_callback).toHaveBeenCalled();
        });

        it('causes the failure callback to be called when the user selects an appellation instead.', function() {
            selectionService.expectWords(success_callback, failure_callback);
            selectionService.succeedAppellationExpectation();
            expect(failure_callback).toHaveBeenCalled();
        });
    });

    describe('the expectAppellation method', function() {
        var success_callback = jasmine.createSpy('success_callback');
        var failure_callback = jasmine.createSpy('failure_callback');
        var e = {target: ''};
        it('causes a callback function to be called when the user selects an appellation.', function() {
            selectionService.expectAppellation(success_callback);
            selectionService.handleSelectAppellation(e);
            expect(success_callback).toHaveBeenCalled();
        });

        it('causes a different callback function to be called when the appellation selection fails.', function() {
            selectionService.expectAppellation(success_callback, failure_callback);
            selectionService.failAppellationExpectation();
            expect(failure_callback).toHaveBeenCalled();
        });

        it('causes the failure callback to be called when the user selects a word instead.', function() {
            selectionService.expectAppellation(success_callback, failure_callback);
            selectionService.succeedWordExpectation();
            expect(failure_callback).toHaveBeenCalled();
        });
    });

    describe('the handleEnter method', function() {
        it('is called when the user presses the enter key on their keyboard', function() {
            selectionService.bindWords();
            selectionService.handleEnter = jasmine.createSpy('handleEnter');
            var event = jQuery.Event("keypress");
            event.which = 13;    // Enter key.
            $(document).trigger(event);

            expect(selectionService.handleEnter).toHaveBeenCalled();
        });
        it('calls handleSelectWord if a word has been selected,', function() {
            selectionService.bindWords();

            var success_callback = jasmine.createSpy('success_callback');
            var failure_callback = jasmine.createSpy('failure_callback');
            selectionService.expectWords(success_callback, failure_callback);

            $('word#4').click();
            selectionService.handleSelectWord = jasmine.createSpy('handleSelectWord');
            selectionService.handleEnter();

            expect(selectionService.handleSelectWord).toHaveBeenCalled();

            describe('which', function() {
                it('causes the success callback to be executed.', function() {
                    expect(selectionService.handleSelectWord).toHaveBeenCalled();
                });
            });
        });

        it('does not call handleSelectWord if no word has been selected.', function() {
            selectionService.bindWords();

            var success_callback = jasmine.createSpy('success_callback');
            var failure_callback = jasmine.createSpy('failure_callback');
            selectionService.expectWords(success_callback, failure_callback);

            selectionService.handleSelectWord = jasmine.createSpy('handleSelectWord');
            selectionService.handleEnter();

            expect(selectionService.handleSelectWord).not.toHaveBeenCalled();
        });
    });

    describe('the handleClick method', function() {
        it('is called when the user clicks on a word.', function() {
            selectionService.handleClick = jasmine.createSpy('handleClick');
            selectionService.bindWords();
            $('word#5').click();
            expect(selectionService.handleClick).toHaveBeenCalled();
        });

        it('adds a word to the selected_words hopper if no word is selected.', function() {
            var words,
                word_success_callback = function(selected_words) { words = selected_words; },
                event = { target: 'word#5', shiftKey: false, };

            selectionService.expectWords(word_success_callback);
            selectionService.handleClick(event);
            selectionService.handleSelectWord();
            expect(words.length).toBe(1);

        });

        it('replaces the current word hopper if the hopper is already occupied.', function() {
            var words,
                word_success_callback = function(selected_words) { words = selected_words; },
                event1 = { target: $('word#3'), shiftKey: false, },
                event2 = { target: $('word#5'), shiftKey: false, };

            selectionService.expectWords(word_success_callback);
            selectionService.handleClick(event1);
            selectionService.handleClick(event2);
            selectionService.handleSelectWord();
            expect(words.length).toBe(1);

        });

        it('extends the current word hopper if the hopper is already occupied and the shift key is depressed.', function() {
            var words,
                word_success_callback = function(selected_words) { words = selected_words; },
                event1 = { target: $('word#3'), shiftKey: false, },
                event2 = { target: $('word#5'), shiftKey: true, };

            selectionService.expectWords(word_success_callback);
            selectionService.handleClick(event1);
            selectionService.handleClick(event2);
            selectionService.handleSelectWord();
            expect(words.length).toBeGreaterThan(1);

        });

        it('highlights the currently selected word.', function() {
            var words,
                word_success_callback = function(selected_words) { words = selected_words; },
                event = { target: 'word#5', shiftKey: false, };

            selectionService.expectWords(word_success_callback);
            selectionService.handleClick(event);
            expect(selectionService.selected_words.hasClass("selected")).toBe(true);

        });

        it('unhighlights previously selected words.', function() {
            var words,
                word_success_callback = function(selected_words) { words = selected_words; },
                event1 = { target: 'word#5', shiftKey: false, },
                event2 = { target: 'word#4', shiftKey: false, };

            selectionService.handleClick(event1);
            expect($('word#5').hasClass('selected')).toBe(true);
            expect($('word#4').hasClass('selected')).toBe(false);
            selectionService.handleClick(event2);
            expect($('word#5').hasClass('selected')).toBe(false);
            expect($('word#4').hasClass('selected')).toBe(true);
        });

        it('succeeds for appellation when an appellation is selected.', function() {
            var appellation,
                appellation_success_callback = function(selected_appellations) { appellation = selected_appellations; },
                event = { target: 'word#1', shiftKey: false, };

            selectionService.expectAppellation(appellation_success_callback);
            selectionService.handleClick(event);

            expect(appellation.id).toBe('2');
            expect(appellation.interpretation).not.toBe(undefined);

        });
    });


});
