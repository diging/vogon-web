/******************************************************************************
 *         Components!
 *****************************************************************************/

var ConceptListItem = {
    props: ['concept'],
    template: `<div class="list-group-item concept-item clearfix" id="concept-{{ concept.uri }}">
                   <div>
                       <a v-on:click="select" style="cursor: pointer;">{{ concept.label }} ({{ concept.authority.name }})</a>
                   </div>
                   <div class="text text-muted">{{ concept.description }}</div>
               </div>`,
    methods: {
        select: function () {
            this.$emit('selectconcept', this.concept);
        },

    }
}

var ConceptSearch = {
    template: `<div id="concept-search" v-on:keyup.enter="search">
                    <div class="form-inline">
                       <div class="form-group" style="width: 20%;">
                           <label class="sr-only">Part of Speech</label>
                           <select class="form-control input-sm"
                                id="concept-search-pos"
                                v-model="pos">
                                <option value="noun">Noun</option>
                                <option value="verb">Verb</option>
                                <option value="">Any</option>
                            </select>
                       </div>
                      <div class="form-group" style="width: 79%;">
                        <div class="input-group input-group-sm" style="width: 100%;">
                            <input type="text" class="form-control input-sm"  style="width: 100%;" v-model="query">
                            <span class="input-group-btn">
                                <a v-if="ready()" class="btn btn-sm glyphicon glyphicon-search" v-on:click="search" style="color: green;"></a>
                                <span v-if="searching" class="btn btn-sm glyphicon glyphicon-hourglass" style="color: orange;"></span>
                                <span v-if="error" class="btn btn-sm glyphicon glyphicon-exclamation-sign" style="color: red;"></span>
                            </span>
                        </div>
                      </div>
                  </div>
                  <div>
                    <div class="form-group">
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" class="checkbox"  style="width: 100%;" v-model="force">
                                Force fresh search
                            </label>
                        </div>
                    </div>
                  </div>
                  <div class="list-group concept-search-list-group">
                      <concept-list-item
                            v-on:selectconcept="selectConcept"
                            v-bind:concept=concept
                            v-for="concept in concepts">
                       </concept-list-item>
                  </div>
              </div>`,
    data: function () {
        return {
            query: '',
            concepts: [],
            searching: false,
            error: false,
            pos: "",
            force: false
        }
    },
    methods: {
        selectConcept: function (concept) {
            // Clear the concept search results.
            this.concepts = [];
            this.$emit('selectconcept', concept);
        },
        ready: function () { // TODO: should be able to recover from errors.
            return !(this.searching || this.error);
        },
        search: function () {
            this.searching = true; // Instant feedback for the user.

            this.$emit('search', this.searching); // emit search to remove concept picker

            // Asynchronous quries are beautiful.
            var self = this; // Need a closure since Concept is global.
            var payload = {
                search: this.query
            };
            if (this.pos != "") {
                payload['pos'] = this.pos;
            }
            if (this.force) {
                payload['force'] = 'force';
            }
            Concept.search(payload).then(function (response) {
                self.concepts = response.body.results;
                self.searching = false;
            }).catch(function (error) {
                console.log("ConceptSearch:: search failed with", error);
                self.error = true;
                self.searching = false;
            });

        }
    },

    components: {
        'concept-list-item': ConceptListItem
    }
}


ConceptCreator = {
    template: `<div class="form">
                    <div class="form-group">
                        <div class="checkbox">
                            <label>
                                <input type="checkbox" placeholder="" id="concept-creator-oath" v-model="oath">
                                I swear that I've searched exhaustively for this concept.
                            </label>
                        </div>
                        <p class="text-muted">
                            Duplicate concepts really muck up the system, so this is a very important step. If you're
                            not sure, search again.
                        </p>
                    </div>
                   <div class="form-group">
                       <label class="control-label">Name</label>
                       <input class="form-control input-sm"
                            type="text"
                            placeholder="This is how other users will find this concept."
                            id="concept-creator-name"
                            v-model="name">
                   </div>
                   <div class="form-group">
                       <label class="control-label">Description</label>
                       <textarea class="form-control input-sm"
                            type="text"
                            placeholder="Make it easy for other users to identify this concept."
                            id="concept-creator-description"
                            v-model="description">
                        </textarea>
                   </div>
                   <div class="form-group">
                       <label class="control-label">Type</label>
                       <select class="form-control input-sm"
                            id="concept-creator-type"
                            v-model="concept_type">
                            <option>---</option>
                            <option v-for="ctype in concept_types" v-bind:value="ctype.uri"">
                                {{ labelType(ctype) }}
                            </option>
                        </select>
                   </div>
                   <div class="form-group">
                       <label class="control-label">Part of Speech</label>
                       <select class="form-control input-sm"
                            id="concept-creator-pos"
                            v-model="pos">
                            <option value="noun">Noun</option>
                            <option value="verb">Verb</option>
                        </select>
                   </div>
                   <div v-if="ready()" class="clearfix">
                       <div class="pull-right btn-group">
                           <a v-if="ready" class="btn btn-success btn-xs" v-on:click="createConcept">
                                Create <span class="glyphicon glyphicon-grain"></span>
                           </a>
                           <span v-if="submitted" class="btn glyphicon glyphicon-hourglass"></span>
                           <span v-if="error" class="btn glyphicon glyphicon-exclamation-sign"></span>
                       </div>
                   </div>
               </div>`,
    data: function () {
        return {
            oath: false,
            name: "",
            description: "",
            concept_type: "",
            pos: "",
            concept_types: [],
            error: false,
            submitted: false
        }
    },
    mounted: function () {
        this.updateTypes();
    },
    watch: {
        name: function () {
            this.tryAgain();
        },
        description: function () {
            this.tryAgain();
        },
        pos: function () {
            this.tryAgain();
        },
        concept_type: function () {
            this.tryAgain();
        }
    },
    methods: {
        ready: function () {
            return (this.oath && this.name.length > 1 && this.description.length > 10 && this.concept_type != "" && !this.submitted);
        },
        tryAgain: function () {
            this.submitted = false;
            this.error = false;
        },
        clear: function () {
            this.oath = false;
            this.name = "";
            this.description = "";
            this.concept_type = "";
            this.pos = "noun";
            this.error = false;
            this.submitted = false;
        },
        createConcept: function () {
            if (this.ready) {
                this.submitted = true; // Immediately prevent further submissions.
                self = this;
                Concept.save({
                    uri: 'generate',
                    label: this.name,
                    description: this.description,
                    pos: this.pos,
                    typed: this.concept_type
                }).then(function (response) {
                    self.clear();
                    self.$emit("createdconcept", response.body);
                }).catch(function (error) {
                    console.log('ConceptCreator:: failed to create concept', error);
                    self.error = true;
                });
            }
        },
        updateTypes: function () {
            self = this; // Closure!
            ConceptType.query().then(function (response) {
                self.concept_types = response.body.results;
            });
        },
        labelType: function (ctype) {
            if (ctype.label) {
                return ctype.label;
            } else {
                if (ctype.authority) {
                    return ctype.authority.name + ': ' + truncateURI(ctype.uri);
                } else {
                    return truncateURI(ctype.uri);
                }
            }
        }
    }
}

DateAppellationCreator = {
    props: ["position", "user", "text", "project"],
    data: function () {
        return {
            year: null,
            month: null,
            day: null,
            submitted: false,
            saving: false

        }
    },
    template: `<div class="appellation-creator">
                    <div class="h4">
                        When is this?
                    </div>
                    <p class="text-warning">
                        Create a date appellation by entering the specific date
                        to which the selected text refers. Specify only the
                        precision warranted by the evidence: for example, you
                        need not enter a month and day if only the year is
                        known.
                    </p>
                    <div>
                        <span class="appellation-creator-offsets">{{ position.startOffset }}&ndash;{{ position.endOffset }}</span>:
                        <span class="appellation-creator-representation">{{ position.representation }}</span>
                    </div>
                    <div class="date-selector form-inline">
                        <input v-model="year" type="number" class="form-control input-sm" placeholder="YYYY" min="-9999" max="9999">
                        <input v-model="month" type="number" class="form-control input-sm" placeholder="MM" min="-100" max="12">
                        <input v-model="day" type="number" class="form-control input-sm" placeholder="DD" min="-100" max="31">
                        <a v-if="ready()" v-on:click="createAppellation" class="btn btn-sm btn-success">Create</a>
                    </div>
                    <div>
                        <a v-on:click="cancel" class="btn btn-xs btn-danger">Cancel</a>
                    </div>
               </div>`,
    methods: {
        ready: function () {
            return (this.year && !(this.day && !this.month));
        },
        reset: function () {
            this.concept = null;
            this.create = false;
            this.submitted = false;
            this.saving = false;
        },
        cancel: function () {
            this.reset();
            this.$emit('cancelappellation');
        },
        createAppellation: function () {
            if (!(this.submitted || this.saving)) {
                // this.submitted = true;      // Prevent multiple submissions.
                // this.saving = true;
                self = this;
                DateAppellation.save({
                    position: {
                        occursIn: this.text.id,
                        position_type: "CO",
                        position_value: [this.position.startOffset,
                            this.position.endOffset
                        ].join(",")
                    },
                    stringRep: this.position.representation,
                    occursIn: this.text.id,
                    createdBy: this.user.id,
                    project: this.project.id,
                    year: this.year,
                    month: this.month,
                    day: this.day
                }).then(function (response) {
                    self.reset();
                    self.$emit('createddateappellation', response.body);
                }).catch(function (error) {
                    this.saving = false;
                    console.log('DateAppellationCreator:: failed to create appellation', error);
                });
            }
        }
    }
}
ConceptPickerItem = {
    props: ['concept'],
    components: {},
    template: `<div class="list-group-item concept-item clearfix" :id="'concept-' + concept.interpretation.uri">
                <div>
                    <a v-on:click="select" style="cursor: pointer;">{{ concept.interpretation_label }} ({{ concept.interpretation.authority }})</a>
                </div>
                <div class="text text-muted">{{ concept.interpretation.description }}</div>
            </div>`,
    methods: {
        select: function () {
            this.$emit('selectconcept', this.concept);
        },

    }
}

ConceptPicker = {
    props: ['appellations'],
    components: {
        'concept-picker-item': ConceptPickerItem
    },
    data: function () {
        return {
            conceptsFinal: [],
            appell: [],
            appellationCount: [],
        }
    },
    template: `<div  class="concept-picker" style="max-height: 50vh; overflow-y: scroll;">
                <concept-picker-item
                    v-on:selectconcept="selectConcept"
                    v-for="concept in conceptsFinal"
                    v-bind:concept=concept>
                </concept-picker-item>
               </div>`,
    methods: {
        selectConcept: function (concept) {
            // Clear the concept search results.
            this.concepts = [];
            this.$emit('selectconcept', concept);
        },
        addConcepts: function (appellationMapEntires) {
            var count = 0
            while (count <= 3) {
                var appellation = appellationMapEntires.next().value;
                if (appellation == null) {
                    break
                }
                if (!this.conceptsFinal.includes(appellation[1][0])) {
                    this.conceptsFinal.push(appellation[1][0]);
                    count++;
                }
            }
        },
        merge: function (appellations) {
            this.conceptsFinal = [];
            this.appell = appellations;
            // Sort by date
            function compare(a, b) {
                if (Date.parse(a.created) > Date.parse(b.created))
                    return -1;
                if (Date.parse(a.created) < Date.parse(b.created))
                    return 1;
                return 0;
            }
            this.appell.sort(compare);
            var appellationMap = new Map();
            // set map items from appell array
            this.appell.forEach(function (item) {
                if (appellationMap.has(item.interpretation.uri)) {
                    appellationMap.get(item.interpretation.uri).push(item);
                } else {
                    appellationMap.set(item.interpretation.uri, [item]);
                }
            });
            var appellationMapEntires = appellationMap.entries();
            // add non-duplicate objects to conceptsFinal sorted by most recent
            this.addConcepts(appellationMapEntires);
            // sort appellationMap by length
            var sortedMap = new Map([...appellationMap.entries()].sort(function (a, b) {
                return b[1].length - a[1].length
            }));
            var sortedMapItems = sortedMap.entries();
            // add non-duplicate objects to conceptsFinal sorted by most occuring
            this.addConcepts(sortedMapItems);
            return this.conceptsFinal;
        },
    },
    created: function () {
        this.merge(this.appellations);

    },
}

AppellationCreator = {
    props: ["position", "user", "text", "project", 'appellations'],
    components: {
        'concept-search': ConceptSearch,
        'concept-creator': ConceptCreator,
        'concept-picker': ConceptPicker
    },
    data: function () {
        return {
            concept: null,
            create: false,
            submitted: false,
            saving: false,
            search: false,
            display: true

        }
    },
    template: `<div class="appellation-creator" style="max-height: 80vh; overflow-y: scroll;">
                    <div class = "h4" v-if="triggered">
                        Select Concept for Text
                     </div>
                    <div class="h4" v-else>
                        What is this?
                        <span class="glyphicon glyphicon-question-sign"
                            v-tooltip="'Create an appellation by attaching a concept from a controlled vocabulary. An appellation is a statement (by you) that the selected text refers to a specific concept.'">
                       </span>
                    </div>
                    <p class="text-warning">

                    </p>
                    <div v-if="triggered">
                        <span class="appellation-creator-offsets">{{ text.title }}</span>
                    </div>
                    <div v-else>
                        <span class="appellation-creator-offsets">{{ position.startOffset }}&ndash;{{ position.endOffset }}</span>:
                        <span class="appellation-creator-representation">{{ position.representation }}</span>
                    </div>
                    <div v-if="concept != null" class="text-warning">{{ concept.label }}
                        <span v-if="concept.authority != null">({{ concept.authority.name }})</span>
                    </div>

                   <div v-if="isSaving()" style="position: absolute; top: 0px;">
                        asdf
                   </div>
                   <div v-if="ready()" class="form-group clearfix">
                        <div class="btn-group pull-right">
                            <a v-on:click="createAppellation" class="btn btn-xs btn-success" v-bind:disabled="isSaving()">
                                Create <span class="glyphicon glyphicon-save"></span>
                            </a>
                        </div>
                   </div>
                   <div v-if="concept == null" class="input-group">
                       <div class="checkbox">
                           <label><input type="checkbox" v-model="create"> I've tried so hard, but I can't find what I'm looking for!</label>
                       </div>
                   </div>
                   <concept-search
                       @search="setSearch"
                       v-if="concept == null && !create"
                       v-on:selectconcept="selectConcept">
                   </concept-search>
                   <concept-creator
                       v-if="create && concept == null"
                       v-on:createdconcept="createdConcept">
                   </concept-creator>
                   <concept-picker
                        v-show="display"
                        v-if="concept == null && !create"
                        v-bind:appellations=appellations
                        v-on:selectconcept="selectConcept">
                   </concept-picker>
                   <div>
                       <a v-on:click="cancel" class="btn btn-xs btn-danger">Cancel</a>
                   </div>
               </div>`,

    watch: {
        search: function () {
            if (this.search == true) {
                this.display = false;
            }
        },
    },
    computed: {
        triggered: function () {
            return store.getters.showConcepts
        }
    },
    methods: {
        reset: function () {
            this.concept = null;
            this.create = false;
            this.submitted = false;
            this.saving = false;
        },
        setSearch: function (search) { // removes concept picker if searching concept to keep it from looking messy
            this.search = search;
        },
        cancel: function () {
            this.reset();
            this.$emit('cancelappellation');
            store.commit("triggerConcepts", false);
        },
        isSaving: function () {
            return this.saving;
        },
        awaitingConcept: function () {
            return (this.concept == null);
        },
        selectConcept: function (concept) {
            this.concept = concept;
        },
        createdConcept: function (concept) {
            this.concept = concept;
            this.create = false;
        },
        createAppellation: function () {
            let stringRep
            /* 
             * may want to change this at somepoint. If this is a concept for a text we set the position values to null
             */
            if (store.getters.showConcepts) {
                this.position.startOffset = null
                this.position.endOffset = null
                stringRep = this.text.title
            } else {
                stringRep = this.position.representation
            }
            if (!(this.submitted || this.saving)) {
                this.submitted = true; // Prevent multiple submissions.
                this.saving = true;
                self = this;
                Appellation.save({
                    position: {
                        occursIn: this.text.id,
                        position_type: "CO",
                        position_value: [this.position.startOffset,
                            this.position.endOffset
                        ].join(",")
                    },
                    stringRep: stringRep,
                    startPos: this.position.startOffset,
                    endPos: this.position.endOffset,
                    occursIn: this.text.id,
                    createdBy: this.user.id,
                    project: this.project.id,
                    interpretation: this.concept.uri || this.concept.interpretation.uri
                }).then(function (response) {
                    self.reset();
                    if (store.getters.showConcepts) {
                        store.commit('setTextAppellation', response.body);
                        if (store.getters.getValidator == 2) {
                            store.commit('setValidator', 0)
                        }
                    }
                    store.commit("triggerConcepts");
                    store.commit("conceptLabel", response.body.interpretation_label);
                    self.$emit('createdappellation', response.body);
                }).catch(function (error) {
                    this.saving = false;
                    console.log('AppellationCreator:: failed to create appellation', error);
                });
            }
        },
        ready: function () {
            if (this.triggered && this.concept) {
                return true
            } else {
                return (this.position.startOffset >= 0 && this.position.endOffset && this.position.representation.trim().length > 0 && this.text.id && this.user.id && this.concept);
            }
        }
    }
}

RelationField = {
    props: ["field", "listener"],
    data: function () {
        return {
            selection: null,
            value_label: null,
            listening: false,
        }
    },
    template: `<div class="form-group relation-field" v-on:keyup.esc="stopListening()">
                    <label class="control-label">{{ field.label }} <span class="text-muted">{{ field.description }}</span></label>
                    <div class="input-group">
                        <input type="text"
                            v-model="value_label"
                            class="form-control input-sm"
                            :id="'relation-part-' + field.part_id"
                            v-bind:placeholder="inputPlaceholder()" />
                        <span class="input-group-btn">
                            <button v-if="selection == null"
                                v-on:click="listen"
                                v-bind:class="{
                                        btn: true,
                                        'btn-sm': true,
                                        'btn-primary': !listening,
                                        'btn-warning': listening,
                                        'btn-default': isBlocked
                                    }">
                                &nbsp;<span v-if="field.type == 'TP'" class=" glyphicon glyphicon-edit"></span>
                                <i v-if="field.type == 'CO'" class="fa fa-i-cursor" aria-hidden="true"></i>
                                <span v-if="field.type == 'DT'" class=" glyphicon glyphicon-calendar"></span>
                            </button>
                            <button
                                v-else
                                v-on:click="clear"
                                class="btn btn-sm btn-success">
                                &nbsp;<span class="glyphicon glyphicon-ok"></span>
                            </button>
                        </span>
                    </div>
               </div>`,
    methods: {
        inputPlaceholder: function () {
            if (this.selection == null && this.listening) {
                if (this.field.type == 'TP') {
                    return 'Select text or existing appellation. Press ESC to cancel.';
                } else if (this.field.type == 'DT') {
                    return 'Select text or existing date appellation. Press ESC to cancel.';
                } else if (this.field.type == 'CO') {
                    return 'Select text. Press ESC to cancel.';
                }
            }
        },
        listen: function () {
            if (!this.listening && !this.isBlocked()) { // Don't bind more than one listener.
                this.listening = true;
                this.$emit('listening', this.field);
                if (this.field.type == 'TP') {
                    AppellationBus.$on('selectedappellation', this.handleSelection);
                } else if (this.field.type == 'CO') {
                    TextBus.$on('selectedtext', this.handleSelection);
                } else if (this.field.type == 'DT') {
                    AppellationBus.$on('selecteddateappellation', this.handleSelection);
                }
            }
        },
        handleSelection: function (selection) {
            this.stopListening();
            this.selection = selection;
            if (this.field.type == 'TP') { // Assume this is an appellation.
                this.value_label = selection.interpretation.label;
            } else if (this.field.type == 'CO') { // Assume it's a position.
                this.value_label = selection.representation;
            } else if (this.field.type == 'DT') {
                this.value_label = selection.dateRepresentation;
            }
            this.$emit('registerdata', this.field, this.selection);
        },
        stopListening: function () {
            if (this.field.type == 'TP') {
                AppellationBus.$off('selectedappellation', this.handleSelection);
            } else if (this.field.type == 'CO') {
                TextBus.$off('selectedtext', this.handleSelection);
            } else if (this.field.type == 'DT') {
                AppellationBus.$off('selecteddateappellation', this.handleSelection);
            }
            this.listening = false;
            this.$emit('donelistening', this.field);
        },
        clear: function () {
            this.selection = null;
            this.value_label = null;
            this.$emit('unregisterdata', this.field);
        },
        // We don't want to interfere with other fields, so we respect the
        //  priority of the current listener, if there is one.
        isBlocked: function () {
            return (this.listener !== undefined && this.listener != null && this.listener != this.field);
        }
    }

}
//

RelationTemplate = {
    props: ["fields", "name", "description"],
    data: function () {
        return {
            listener: null,
        };
    },
    components: {
        'relation-field': RelationField
    },
    template: `<div class="form relation-form">
                    <div class="h5">{{ name }}</div>
                    <p class="text-warning">{{ description }}</p>
                    <relation-field
                        v-on:listening="fieldIsListening"
                        v-on:donelistening="fieldIsDoneListening"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        v-for="field in fields"
                        v-bind:field=field
                        v-bind:listener=listener></relation-field>
               </div>`,
    methods: {
        // Since we only want one field to listen for an appellation at a time,
        //  we keep track of the first field to announce that they are
        //  listening. All other RelationField instances are expected to respect
        //  that listener, and not start listening until the current field is
        //  done.
        fieldIsListening: function (listeningField) {
            this.listener = listeningField;
            if (listeningField.type == 'CO') this.$emit('fieldislisteningfortext');
        },
        fieldIsDoneListening: function (listeningField) {
            this.listener = null;
            if (listeningField.type == 'CO') this.$emit('fieldisdonelisteningfortext');
        },
        registerData: function (field, data) {
            this.$emit('registerdata', field, data);
        },
        unregisterData: function (field) {
            this.$emit('unregisterdata', field);
        }
    }
}


RelationDateAssignment = {
    props: ["listener"],
    data: function () {
        return {
            startTemplate: {
                "part_field": "start",
                "part_id": -1,
                "concept_label": null,
                "evidence_required": true,
                "description": "Please indicate the date when this relation began.",
                "type": "DT",
                "concept_id": null,
                "label": "Started"
            },
            endTemplate: {
                "part_field": "end",
                "part_id": -1,
                "concept_label": null,
                "evidence_required": true,
                "description": "Please indicate the date when this relation ended.",
                "type": "DT",
                "concept_id": null,
                "label": "Ended"
            },
            occurTemplate: {
                "part_field": "occur",
                "part_id": -1,
                "concept_label": null,
                "evidence_required": true,
                "description": "Please indicate the date when this relation occurred or was true.",
                "type": "DT",
                "concept_id": null,
                "label": "Occurred"
            },
            collectStarted: false,
            collectOccurred: false,
            collectEnded: false
        }
    },
    components: {
        'relation-field': RelationField
    },
    template: `<div class="relation-date-bits">
                    <relation-field v-if="collectStarted"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        v-bind:listener=listener
                        v-bind:field=startTemplate
                        v-on:listening="fieldIsListening"
                        v-on:donelistening="fieldIsDoneListening">
                    </relation-field>
                    <relation-field v-if="collectOccurred"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        v-bind:listener=listener
                        v-bind:field=occurTemplate
                        v-on:listening="fieldIsListening"
                        v-on:donelistening="fieldIsDoneListening">
                    </relation-field>
                    <relation-field v-if="collectEnded"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        v-bind:listener=listener
                        v-bind:field=endTemplate
                        v-on:listening="fieldIsListening"
                        v-on:donelistening="fieldIsDoneListening">
                    </relation-field>
                    <a v-on:click="toggleCollectStarted"
                        v-bind:class="{
                                'btn': true,
                                'btn-xs': true,
                                'btn-success': !collectStarted,
                                'btn-danger': collectStarted
                            }">
                            <span v-bind:class="{
                                    'glyphicon': true,
                                    'glyphicon-calendar': !collectStarted,
                                    'glyphicon-remove': collectStarted
                                }"></span> Started</a>
                    <a v-on:click="toggleCollectOccurred"
                        v-bind:class="{
                                'btn': true,
                                'btn-xs': true,
                                'btn-success': !collectOccurred,
                                'btn-danger': collectOccurred
                            }">
                            <span v-bind:class="{
                                    'glyphicon': true,
                                    'glyphicon-calendar': !collectOccurred,
                                    'glyphicon-remove': collectOccurred
                                }"></span> Occurred
                    </a>
                    <a v-on:click="toggleCollectEnded"
                        v-bind:class="{
                                'btn': true,
                                'btn-xs': true,
                                'btn-success': !collectEnded,
                                'btn-danger': collectEnded
                            }">
                            <span v-bind:class="{
                                    'glyphicon': true,
                                    'glyphicon-calendar': !collectEnded,
                                    'glyphicon-remove': collectEnded
                                }"></span> Ended</a>
               </div>`,
    methods: {
        toggleCollectStarted: function () {
            this.collectStarted = !this.collectStarted;
        },
        toggleCollectOccurred: function () {
            this.collectOccurred = !this.collectOccurred;
        },
        toggleCollectEnded: function () {
            this.collectEnded = !this.collectEnded;
        },
        fieldIsListening: function (listeningField) {
            this.listener = listeningField;
            if (listeningField.type == 'CO') this.$emit('fieldislisteningfortext');
        },
        fieldIsDoneListening: function (listeningField) {
            this.listener = null;
            if (listeningField.type == 'CO') this.$emit('fieldisdonelisteningfortext');
        },
        registerData: function (field, data) {
            this.$emit('registerdata', field, data);
        },
        unregisterData: function (field) {
            this.$emit('unregisterdata', field);
        }
    }
}


RelationCreator = {
    props: ["text", "project", "user", "template"],
    data: function () {
        return {
            field_data: {},
            ready: false,
            error: false,
            start: null,
            end: null,
            occur: null
        }
    },
    computed: {
        fields: function () {
            return this.template.fields;
        },
        description: function () {
            return this.template.description;
        },
        name: function () {
            return this.template.name;
        },
        id: function () {
            return this.template.id;
        }
    },
    components: {
        'relation-template': RelationTemplate,
        'relation-date-assignment': RelationDateAssignment
    },
    template: `<div class="relation-creator">
                    <relation-date-assignment
                        v-on:fieldislisteningfortext="fieldIsListeningForText"
                        v-on:fieldisdonelisteningfortext="fieldIsDoneListeningForText"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        >
                    </relation-date-assignment>
                    <relation-template
                        v-on:fieldislisteningfortext="fieldIsListeningForText"
                        v-on:fieldisdonelisteningfortext="fieldIsDoneListeningForText"
                        v-on:registerdata="registerData"
                        v-on:unregisterdata="unregisterData"
                        v-bind:fields=fields
                        v-bind:description=description
                        v-bind:name=name>
                    </relation-template>
                    <div v-if="error" class="alert alert-danger alert-xs">
                        Whoops! Something went wrong.
                    </div>
                    <div class="clearfix">
                        <div v-if="ready" class="pull-right">
                            <a v-on:click="create" class="btn btn-xs btn-success">Create</a>
                        </div>
                        <div>
                            <a v-on:click="cancel" class="btn btn-xs btn-danger">Cancel</a>
                        </div>
                    </div>


               </div>`,
    methods: {
        fieldIsListeningForText: function () {
            this.$emit('fieldislisteningfortext');
        },
        fieldIsDoneListeningForText: function () {
            this.$emit('fieldisdonelisteningfortext');
        },
        registerData: function (field, data) {
            this.field_data[this.fieldHash(field)] = data;
            this.ready = this.readyToCreate();
        },
        unregisterData: function (field, data) {
            delete(this.field_data[this.fieldHash(field)]);
            this.ready = this.readyToCreate();
        },
        readyToCreate: function () {
            var ready = true;
            self = this;
            this.fields.forEach(function (field) {
                if (self.field_data[self.fieldHash(field)] == undefined) {
                    ready = false;
                }
            })
            return ready;
        },
        // Relation fields don't have unique identifiers, so we create them.
        fieldHash: function (field) {
            return [field.part_id, field.part_field].join('.');
        },
        prepareSubmission: function () {
            self = this;
            this.fields.forEach(function (field) {
                if (field.type == "TP" || field.type == 'DT') { // Open concept; expects appellation.
                    field.appellation = self.field_data[self.fieldHash(field)];

                } else if (field.type == "CO") { // Expects text only.
                    var position = self.field_data[self.fieldHash(field)]
                    field.position = {
                        occursIn_id: self.text.id,
                        position_type: "CO",
                        position_value: [position.startOffset,
                            position.endOffset
                        ].join(",")
                    };
                    field.data = {
                        tokenIds: null,
                        stringRep: position.representation
                    };
                }
            });
            ['start', 'end', 'occur'].forEach(function (temporal_part) {
                var key = '-1.' + temporal_part;
                if (key in self.field_data) {
                    self[temporal_part] = self.field_data[key];
                }
            });
        },
        cancel: function () {
            this.$emit('cancelrelation');
        },
        create: function () {
            this.prepareSubmission();
            self = this;
            RelationTemplateResource.create({
                id: this.id
            }, {
                fields: this.fields,
                occursIn: this.text.id,
                createdBy: this.user.id,
                project: this.project.id
            }).then(function (response) {
                this.ready = false;
                self.$emit('createdrelation', response.body);
            }).catch(function (error) {
                console.log('RelationTemplateResource:: failed miserably', error);
                self.error = true;
                self.ready = false;
            }); // TODO: implement callback and exception handling!!
        }
    }
}

RelationTemplateSelector = {
    data: function () {
        return {
            templates: [],
            query: "",
            searching: false
        }
    },
    template: `<div class="relation-template-selector">
                    <div class="form-group" v-on:keyup.enter="search">
                        <div class="input-group">
                            <input type="text"
                                class="form-control input-sm"
                                v-model="query"
                                placeholder="Search for a relation template..." />
                            <div class="input-group-btn">
                                <a v-on:click="search" class="btn btn-sm btn-success">
                                    &nbsp;<span v-if="!searching" class="glyphicon glyphicon-search"></span>
                                    <span v-if="searching" class="glyphicon glyphicon-hourglass"></span>
                                </a>
                            </div>
                        </div>
                    </div>
                    <p class="text-muted">
                        Relation templates are pre-configured "formulas" for encoding relational information
                        in a text.
                    </p>
                    <div class="list-group" v-if="showingTemplates()" style="max-height: 300px; overflow-y: scroll;">
                        <a v-on:click="selectTemplate(template)"
                            v-for="template in templates"
                            v-bind:template=template
                            class="list-group-item relationtemplate-item">
                            <div>
                                <strong>{{ template.name }}</strong> <span class="text-muted">{{ template.description }}</span>
                            </div>
                        </a>
                    </div>
                    <div v-if="showingTemplates()">
                        <a v-on:click="clear" class="btn btn-xs btn-danger">Cancel</a>
                    </div>
               </div>`,
    methods: {
        search: function () {
            this.searching = true;
            self = this;
            RelationTemplateResource.query({
                search: this.query,
                format: "json",
                all: true
            }).then(function (response) {
                self.templates = response.body.templates;
                self.searching = false;
            }).catch(function (error) {
                console.log('Failed to get relationtemplates', error);
                self.searching = false;
            });
        },
        selectTemplate: function (template) {
            this.$emit('selectedtemplate', template);
        },
        clear: function () {
            this.templates = [];
        },
        showingTemplates: function () {
            return this.templates.length > 0;
        }
    }
}



Appellator = new Vue({
    el: '#appellator',
    store,
    components: {
        'appellation-list': AppellationList,
        'relation-list': RelationList,
        'text-display': TextDisplay,
        'appellation-creator': AppellationCreator,
        'relation-creator': RelationCreator,
        'relation-template-selector': RelationTemplateSelector,
        'date-appellation-creator': DateAppellationCreator
    },
    template: `#annotation-template`,
    data: function () {
        return {
            appellations: [],
            dateappellations: [],
            relations: [],
            selected: null,
            selected_text: null,
            user: {
                id: USER_ID,
                username: USER_NAME
            },
            text: {
                id: TEXT_ID,
                title: TEXT_TITLE
            },
            project: {
                id: PROJECT_ID,
                name: PROJECT_NAME
            },
            sidebarShown: false,
            template: null,
            creating_relation: true,
            text_listener: null,
            sidebar: 'relations',
            create_date_appellation: false,
            swimmerPosition: 'static',
            swimmerTop: 0,
            swimmerRef: 0,
            swimmerLeft: -2,
            swimmerWidth: 0,
            submitAppellationClicked: false,
            massAssignmentFailed: false
        }
    },
    mounted: function () {
        this.updateAppellations();
        this.updateRelations();
        store.commit('setAppellations', this.appellations);
        this.updateDateAppellations();
        this.updateSwimRef();
        this.handleScroll();
        //needs to be called in mounted.
        this.watchStoreForConcepts();
        this.watchStoreForAssignmentFailed();
    },
    created() {
        window.addEventListener('scroll', this.handleScroll);
        window.addEventListener('resize', this.handleScroll);
        var self = this;
        document.getElementById('graphContainer').onmouseup = function () {
            self.updateSwimRef();
            self.handleScroll();
        }
    },
    destroyed() {
        window.removeEventListener('scroll', this.handleScroll);
        window.removeEventListener('resize', this.handleScroll);
    },
    watch: {
        sidebar: function () {
            // remove submit button if sidebar is not showing submitAllAppellations 
            if (!(this.sidebar == 'submitAllAppellations')) {
                this.submitAppellationClicked = false;
            }
        },
        appellations: function () {
            this.filterTextAppellationFromAppellationList();
        }
    },
    computed: {
        fields: function () {
            return this.template.fields;
        },
    },
    methods: {
        /*************************************************
         * Start Methods to create relationships to text *
         *************************************************/
        watchStoreForConcepts: function () {
            store.watch(
                (state) => {
                    return store.getters.showConcepts;
                },
                (val) => {
                    if (val) {
                        //FIXME: This should set selected text to the actual text id
                        this.selected_text = this.text.title;
                        this.text_listener == null;
                    } else {
                        this.unselectText();
                    }
                }, {
                    deep: true
                }
            );
        },
        watchStoreForAssignmentFailed: function () {

            store.watch(
                (state) => {
                    return store.getters.getAssignmentFailed;
                },
                (val) => {
                    if (val == true) {
                        this.massAssignmentFailed = true
                    }
                },
            );
        },
        registerData: function (field, data) {
            this.field_data[this.fieldHash(field)] = data;
            this.ready = this.readyToCreate();
        },
        filterTextAppellationFromAppellationList: function () {
            let i = this.appellations.length - 1;
            /* 
             * Remove appellations that have the string represenation that matches the text title
             * this assumes the appellation is that of the text and we remove it as to not make a
             * relation to itself. You must iterate backwards when removing items from an array to
             * prevent indexing errors.
             */
            while (i >= 0) {
                try {
                    if (this.appellations[i].stringRep == this.text.title) {
                        store.commit('setTextAppellation', this.appellations[i])
                        store.commit("conceptLabel", this.appellations[i].interpretation_label);
                        this.appellations.splice(i, 1)
                        store.commit('removeAppellation', i);
                    }
                } catch (error) {
                    console.log(error);
                }
                i--;
            }
        },
        validateCreateRelationsToTextData: function () {
            if (store.getters.getTemplate == null) {
                return 1;
            } else if (store.getters.getTextAppellation.length == 0) {
                return 2;
            } else if (store.getters.getAppellationsToSubmit.length == 0) {
                return 3;
            } else {
                return 0
            }
        },
        createRelationsFromText: function () {
            self = this;
            let validator = this.validateCreateRelationsToTextData();
            if (validator > 0) {
                store.commit('setValidator', validator)
                return
            }
            this.filterTextAppellationFromAppellationList();
            RelationTemplateResource.text({
                id: store.getters.getTemplate.id
            }, {
                appellations: store.getters.getAppellationsToSubmit,
                textAppellation: store.getters.getTextAppellation,
                start: this.start,
                end: this.end,
                occur: this.occur,
                part_id: store.getters.getTemplate.template_parts[0].id,
                occursIn: this.text.id,
                createdBy: this.user.id,
                project: this.project.id
            }).then(function (response) {
                self.ready = false;
                self.sidebarShown = false;
                self.sidebar = 'relations';
                store.commit('resetCreateAppelltionsToText');
            }).catch(function (error) {
                console.log('RelationTemplateResource:: failed miserably', error);
                self.error = true;
                self.ready = false;
                store.commit('massAppellationAssignmentFailed');
            }); // TODO: implement callback and exception handling!!
        },
        //TODO: Change function to SubmitAllAppellations
        showSubmitAllAppellationsSidebar: function () {
            this.sidebar = 'submitAllAppellations';
            this.submitAppellationClicked = true;
        },
        /***********************************************
         * End Methods to create relationships to text *
         ***********************************************/
        getSwimmerWidth: function () {
            var shadow_elem = document.getElementById('shadow-swimlane');
            if (shadow_elem == null) {
                return 0;
            } else {
                return shadow_elem.clientWidth + 2;
            }
        },
        handleScroll: function () {
            var shadow_elem = document.getElementById('shadow-swimlane');
            var swimmer = document.getElementById('sticky-swimlane');
            var scrolled = this.swimmerRef - window.scrollY;
            this.swimmerWidth = shadow_elem.clientWidth + 2;
            if (scrolled < 0) {
                this.swimmerTop = 0;
            } else {
                this.swimmerTop = this.swimmerRef - window.scrollY;
            }
        },
        updateSwimRef: function () {
            var shadow_elem = document.getElementById('shadow-swimlane');
            this.swimmerRef = getOffsetTop(shadow_elem);
        },
        toggleDateAppellation: function () {
            this.create_date_appellation = !this.create_date_appellation;
        },
        fieldIsListeningForText: function () {
            this.text_listener = true;
        },
        fieldIsDoneListeningForText: function () {
            this.text_listener = null;
        },
        selectedTemplate: function (template) {
            this.template = template;
        },
        createdRelation: function (relation) {
            this.template = null;
            this.updateRelations();
            this.updateAppellations();
        },
        cancelRelation: function () {
            this.template = null;
        },
        sidebarIsShown: function () {
            return this.sidebarShown;
        },
        showSidebar: function () {
            this.sidebarShown = true;
        },
        hideSidebar: function () {
            this.sidebarShown = false;
        },
        selectConcept: function (concept) {
            this.selected_concept = concept;
        },
        hideAllAppellations: function () {
            this.appellations.forEach(function (a) {
                a.visible = false;
            });
        },
        showAllAppellations: function () {
            this.appellations.forEach(function (a) {
                a.visible = true;
            });
        },
        showAppellation: function (appellation) {
            this.appellations.forEach(function (a) {
                if (a.id == appellation.id) a.visible = true;
            });
        },
        hideAppellation: function (appellation) {
            this.appellations.forEach(function (a) {
                if (a.id == appellation.id) a.visible = false;
            });
        },
        hideAllDateAppellations: function () {
            this.dateappellations.forEach(function (a) {
                a.visible = false;
            });
        },
        showAllDateAppellations: function () {
            this.dateappellations.forEach(function (a) {
                a.visible = true;
            });
        },
        showDateAppellation: function (appellation) {
            this.dateappellations.forEach(function (a) {
                if (a.id == appellation.id) a.visible = true;
            });
        },
        hideDateAppellation: function (appellation) {
            this.dateappellations.forEach(function (a) {
                if (a.id == appellation.id) a.visible = false;
            });
        },
        scrollToAppellation: function (appellation) {
            window.scrollTo(0, getTextPosition(appellation.position).top);
        },
        selectAppellation: function (appellation) {
            this.appellations.forEach(function (a) {
                a.selected = (a.id == appellation.id);
            });
            AppellationBus.$emit('selectedappellation', appellation);
            EventBus.$emit('cleartextselection');
            this.unselectText();
            this.unselectDateAppellation();
            this.scrollToAppellation(appellation);
        },
        selectDateAppellation: function (appellation) {
            this.dateappellations.forEach(function (a) {
                a.selected = (a.id == appellation.id);
            });
            AppellationBus.$emit('selecteddateappellation', appellation);
            EventBus.$emit('cleartextselection');
            this.unselectText();
            this.unselectAppellation();
            this.scrollToAppellation(appellation);
        },
        selectAppellationsById: function (appellation_ids) {
            this.appellations.forEach(function (appellation) {
                appellation.selected = (appellation_ids.indexOf(appellation.id) > -1);
            });
        },
        unselectAppellation: function () {
            this.appellations.forEach(function (a) {
                a.selected = false;
            });
        },
        unselectDateAppellation: function () {
            this.dateappellations.forEach(function (a) {
                a.selected = false;
            });
        },
        selectText: function (position) {
            this.unselectAppellation();
            if (!this.text_listener) {
                this.selected_text = position;
            }
            TextBus.$emit('selectedtext', position);
        },
        unselectText: function () {
            this.selected_text = null;
        },
        textIsSelected: function () {
            return this.selected_text != null && this.text_listener == null;
        },
        cancelAppellation: function () {
            this.selected_text = null;
        },
        createdAppellation: function (appellation) {
            self = this;
            var offsets = appellation.position.position_value.split(',');
            appellation.position.startOffset = offsets[0];
            appellation.position.endOffset = offsets[1];
            appellation.visible = true;
            appellation.selected = false;
            self.appellations.push(appellation);
            self.selectAppellation(appellation);
            this.selected_text = null;
            this.updateAppellations(); // call update appellations when a new appelation is created to update list
        },
        createdDateAppellation: function (appellation) {
            self = this;
            var offsets = appellation.position.position_value.split(',');
            appellation.position.startOffset = offsets[0];
            appellation.position.endOffset = offsets[1];
            appellation.visible = true;
            appellation.selected = false;
            self.dateappellations.push(appellation);
            self.selectDateAppellation(appellation);
            this.selected_text = null;
        },
        updateAppellations: function (callback) {
            // "CO" is the "character offset" DocumentPosition type. For image
            //  annotation this should be changed to "BB".
            var self = this;
            Appellation.query({
                position_type: "CO",
                text: this.text.id,
                limit: 500,
                project: this.project.id
            }).then(function (response) {
                // DocumentPosition.position_value is represented with a
                //  TextField, so serialized as a string. Start and end offsets
                //  should be comma-delimited.

                self.appellations = response.body.results.map(function (appellation) {
                    var offsets = appellation.position.position_value.split(',');
                    appellation.position.startOffset = offsets[0];
                    appellation.position.endOffset = offsets[1];
                    appellation.visible = true;
                    appellation.selected = false;
                    return appellation;

                });
                if (callback) callback(response);
            });
        },
        updateDateAppellations: function (callback) {
            // "CO" is the "character offset" DocumentPosition type. For image
            //  annotation this should be changed to "BB".
            var self = this;
            DateAppellation.query({
                position_type: "CO",
                text: this.text.id,
                limit: 500,
                project: this.project.id
            }).then(function (response) {
                // DocumentPosition.position_value is represented with a
                //  TextField, so serialized as a string. Start and end offsets
                //  should be comma-delimited.
                self.dateappellations = response.body.results.map(function (appellation) {
                    var offsets = appellation.position.position_value.split(',');
                    appellation.position.startOffset = offsets[0];
                    appellation.position.endOffset = offsets[1];
                    appellation.visible = true;
                    appellation.selected = false;
                    return appellation;
                });
                if (callback) callback(response);
            });
        },
        selectRelation: function (relation) {
            this.selected_relation = relation;
            this.selected = null;
            this.relations.forEach(function (r) {
                r.selected = (r.id == relation.id);
            });
            var appellation_ids = relation.appellations.map(function (appellation) {
                return appellation.id;
            });
            this.appellations.forEach(function (appellation) {
                appellation.selected = (appellation_ids.indexOf(appellation.id) > -1);
            });
            var dateappellation_ids = relation.date_appellations.map(function (appellation) {
                return appellation.id;
            });
            this.dateappellations.forEach(function (appellation) {
                appellation.selected = (dateappellation_ids.indexOf(appellation.id) > -1);
            });
        },
        updateRelations: function (callback) {
            self = this;
            Relation.query({
                text: this.text.id,
                limit: 500,
                project: this.project.id
            }).then(function (response) {
                self.relations = response.body.results;
                if (callback) {
                    callback(response);
                }
            }).catch(function (error) {
                console.log('failed to get relations', error);
            });
            if (reloadGraph) {
                reloadGraph();
            }
        },
        showRelationsSidebar: function () {
            this.sidebar = 'relations';
        },
        showAppellationsSidebar: function () {
            this.sidebar = 'appellations';
        },
        showDateAppellationsSidebar: function () {
            this.sidebar = 'dateappellations';
        }

    }
});