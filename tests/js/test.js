describe('appellationService functions:', function() {
    var mySpy = {
        query: function() {
            return [{id: 0}, {id: 1}, {id: 2}];
        }
    }

    var appellationService;
    beforeEach(module('annotationApp'));

    beforeEach(module(function($provide) {
        $provide.value("Appellation", mySpy);
    }));

    beforeEach(inject(function(_appellationService_){
        appellationService = _appellationService_;
    }));

    describe('the indexAppellation method', function() {
        var dummyAppellation = {
            id: 0,
            interpretation: 5,
        }
        it('indexes Appellations by their interpretation (id)', function() {
            appellationService.indexAppellation(dummyAppellation);
            expect(appellationService.appellationHash[5].length).toBe(1);
            expect(appellationService.appellationHash[5][0]).toEqual(jasmine.objectContaining(dummyAppellation));
        });
        it('indexes Appellations by their own ids, as well', function() {
            appellationService.indexAppellation(dummyAppellation);
            expect(appellationService.appellationsById[0]).toEqual(jasmine.objectContaining(dummyAppellation));
        });
    });

    describe('the insertAppellations method', function() {
        var appellations = [{id: 0, interpretation: 20}, {id: 1, interpretation: 2}];
        it('sets the `appellations` property with the array provided', function() {
            appellationService.insertAppellations(appellations);
            
            expect(appellationService.appellations.length).toBe(2);
        });

        it('indexes each Appellation in the array provided', function() {
            appellationService.insertAppellations(appellations);

            expect(Object.keys(appellationService.appellationHash)).toContain('20')
            expect(Object.keys(appellationService.appellationHash)).toContain('2')
            expect(Object.keys(appellationService.appellationsById)).toContain('0')
            expect(Object.keys(appellationService.appellationsById)).toContain('1')
        });
    });
});
