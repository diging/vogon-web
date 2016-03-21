describe('appellationService functions:', function() {
    // Mocks the Appellation Resource.
    var appellationSpy = function(data) {
        return this;
    }
    appellationSpy.query = function() {
        return { results: [{id: 0}, {id: 1}, {id: 2}] };
    }
    appellationSpy.get = function() {
        return {
            then: function(callback) {
                return callback({id: 3, interpretation: 42});
            }
        }
    }
    appellationSpy.prototype.$save = function(data) {
        if (data === undefined) var data = {};
        return {
            then: function(callback) {
                data.id = 4;
                return callback(data);
            }
        }
    }


    var appellationService;
    beforeEach(module('annotationApp'));

    beforeEach(module(function($provide) {
        $provide.value("Appellation", appellationSpy);
    }));

    beforeEach(inject(function(_appellationService_, _Appellation_){
        Appellation = _Appellation_
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

    describe('the removeAppellation method', function() {
        var appellations = [{id: 0, interpretation: 20}, {id: 1, interpretation: 2}];

        it('removes an Appellation from the list of appellations', function() {
            appellationService.insertAppellations(appellations);
            appellationService.removeAppellation(1);

            expect(appellationService.appellations.length).toBe(1);
        });

        it('removes an Appellation from the interpretation index', function() {
            appellationService.insertAppellations(appellations);
            appellationService.removeAppellation(1);

            expect(Object.keys(appellationService.appellationHash)).not.toContain('2')
        });

        it('removes an Appellation from the id index', function() {
            appellationService.insertAppellations(appellations);
            appellationService.removeAppellation(1);

            expect(Object.keys(appellationService.appellationsById)).not.toContain('1')
        });
    });

    describe('the getAppellation method', function() {
        var appellations = [{id: 0, interpretation: 20}, {id: 1, interpretation: 2}];
        describe('(when an appellation is already loaded)', function() {
            it('does not call Appellation.get()', function() {
                appellationService.insertAppellations(appellations);
                spyOn(Appellation, 'get').and.callThrough();

                appellationService.getAppellation(1);

                expect(Appellation.get).not.toHaveBeenCalled();
            });
        });

        describe('(when an appellation is not already loaded)', function() {
            it('calls Appellation.get()', function() {
                appellationService.insertAppellations(appellations);
                spyOn(Appellation, 'get').and.callThrough();

                appellationService.getAppellation(3);
                expect(Appellation.get).toHaveBeenCalled();
            });
        });
    });
    describe('the createAppellation method', function() {
        it('calls Appellation.prototype.$save()', function() {
            spyOn(Appellation.prototype, '$save').and.callThrough();
            appellationService.createAppellation({interpretation: 51});
            expect(Appellation.prototype.$save).toHaveBeenCalled();
        });
    });


});
