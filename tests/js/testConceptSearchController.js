describe('ConceptSearchController functions:', function() {
    var conceptSearchController;
    var conceptSpy = function(data) {
        return this;
    }

    conceptSpy.list = function() {
        return {
            $promise: {
                then: function(callback) {
                    return callback([
                        {label: 'TestConcept', type: 'TestType', description: 'Describe'},
                        {label: 'TestConcept2', type: 'TestType2', description: 'Describeddd'},
                    ]);
                }
            }
        }
    }
    conceptSpy.query = function() {
        return {
            $promise: {
                then: function(callback) {
                    return callback([
                        {label: 'TestConcept3', type: 'TestType', description: 'Described'},
                        {label: 'TestConcept4', type: 'TestType2', description: 'Describeddd'},
                        {label: 'TestConcept5', type: 'TestType2', description: 'Describeddd...'},
                    ]);
                }
            }
        }
    }


    beforeEach(module('annotationApp'));
    var scope, httpBackend, createController, Concept;

    beforeEach(module(function($provide) {
        $provide.value("Concept", conceptSpy);
    }));


    beforeEach(inject(function ($rootScope, $controller, _Concept_) {
        Concept = _Concept_;
        spyOn(Concept, 'list').and.callThrough();
        spyOn(Concept, 'query').and.callThrough();
        scope = $rootScope.$new();
        controller = $controller('ConceptSearchController', {
            '$scope': scope
        });

    }));

    it('loads some concepts by default.', function() {
        expect(Concept.list).toHaveBeenCalled();
        expect(scope.concepts.length).toBeGreaterThan(0);
    });

    describe('the search method', function() {
        it('calls Concept.query if the user has entered more than two characters.', function() {
            scope.query = 'Wha';
            scope.search();
            expect(Concept.query).toHaveBeenCalled();
        });
        it('does not call Concept.query if the user has entered fewer than three characters.', function() {
            scope.query = 'Wh';
            scope.search();
            expect(Concept.query).not.toHaveBeenCalled();
        });
        it('updates the concepts model.', function() {
            expect(scope.concepts.length).toBe(2);
            scope.query = 'Wha';
            scope.search();
            expect(scope.concepts.length).toBe(3);
        });
    });

    describe('the select method', function() {
        it('sets the concept model.', function() {
            expect(scope.concept).toBe(null);
            scope.select(scope.concepts[0]);
            expect(scope.concept).not.toBe(null);
        });
        it('clears the concepts (list) model.', function() {
            expect(scope.concepts.length).toBeGreaterThan(0);
            scope.select(scope.concepts[0]);
            expect(scope.concepts.length).not.toBeGreaterThan(0);
        });
    });

    describe('the conceptSelected method', function() {
        it('indicates whether or not a concept has been selected.', function() {
            expect(scope.conceptSelected()).toBe(false);
            scope.select(scope.concepts[0]);
            expect(scope.conceptSelected()).toBe(true);
            scope.reset();
            expect(scope.conceptSelected()).toBe(false);
        });
    });

    describe('the startCreatingConcept method', function() {
        it('reveals the concept creation menu.', function() {
            scope.startCreatingConcept();
            expect(scope.hideCreateConcept).toBe(false);
        });
    });


});
