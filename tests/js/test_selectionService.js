describe('selectionService functions:', function() {
    // Mocks the Concept Resource.
    var conceptSpy = function(data) {
        return this;
    }


    var selectionService;
    beforeEach(module('annotationApp'));

    beforeEach(module(function($provide) {  // Insert the mocked Concept.
        $provide.value("Concept", conceptSpy);
    }));

    beforeEach(inject(function(_selectionService_, _Concept_){
        Concept = _Concept_
        selectionService = _selectionService_;
    }));

    describe('the indexAppellation method', function() {
        it('', function() {
            expect(1).toBe(1);
        });
    });
});
