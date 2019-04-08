var AppellationListItem = {
    props: ['appellation', 'sidebar', 'index'],
    template: `<li v-bind:class="{
						'list-group-item': true,
						'appellation-list-item': true,
						'appellation-selected': isSelected()
					}">
					
				<span class="pull-right text-muted btn-group">
					<a class="btn btn-xs" v-on:click="select">
						<span class="glyphicon glyphicon-hand-down"></span>
					</a>
					<a class="btn btn-xs" v-on:click="toggle">
						<span v-if="appellation.visible" class="glyphicon glyphicon glyphicon-eye-open"></span>
						<span v-else class="glyphicon glyphicon glyphicon-eye-close"></span>
					</a>
				</span>
				
				{{ label() }}
				<div class="text-warning">
					<input v-if="sidebar == 'submitAllAppellations'" type="checkbox" v-model="checked" aria-label="...">
					Created by <strong>{{ getCreatorName(appellation.createdBy) }}</strong> on {{ getFormattedDate(appellation.created) }}
				</div>
				</li>`,
    data: function () {
        return {
            checked: true,
            canUncheckAll: false,
            canCheckAll: false
        }
    },
    mounted: function () {
        this.watchUncheckStore();
        this.watchCheckStore();
        this.$root.$on('appellationClicked', data => {
            if (data === this.appellation) {
                this.checked = !this.checked;
            }
        });
    },
    watch: {
        checked: function () {
            if (this.checked == false) {
                store.commit('removeAppellation', this.index);
                store.commit('setSelectFalse')
            } else {
                if (store.getters.getValidator == 3) {
                    store.commit('setValidator', 0);
                }
                store.commit('addAppellation', this.appellation)
                store.commit('setDeselectFalse')
            }
        },

    },
    methods: {
        watchUncheckStore: function () {
            store.watch(
                (state) => {
                    return store.getters.getDeselect
                },
                (val) => {
                    if (val) {
                        this.uncheckAll()
                        this.canCheckAll = true;
                    }
                },
            );
        },
        watchCheckStore: function () {
            store.watch(
                (state) => {
                    return store.getters.getSelect
                },
                (val) => {
                    if (val) {
                        this.checkAll()
                    }
                },
            );
        },

        uncheckAll: function () {
            this.checked = false;
        },
        checkAll: function () {
            this.checked = true;
        },
        hide: function () {
            this.$emit("hideappellation", this.appellation);
        },
        show: function () {
            this.$emit("showappellation", this.appellation);
        },
        toggle: function () {
            if (this.appellation.visible) {
                this.hide();
            } else {
                this.show();
            }
        },
        isSelected: function () {
            return this.appellation.selected;
        },
        select: function () {
            this.$emit('selectappellation', this.appellation);
        },
        label: function () {
            if (this.appellation.interpretation) {
                return this.appellation.interpretation.label;
            } else if (this.appellation.dateRepresentation) {
                return this.appellation.dateRepresentation;
            }
        },
        getCreatorName: function (creator) {
            if (creator.id == USER_ID) {
                return 'you';
            } else {
                return creator.username;
            }
        },
        getFormattedDate: function (isodate) {
            return moment(isodate).format('dddd LL [at] LT');
        }

    }
}


AppellationList = {
    props: ['appellations', 'sidebar'],
    template: `
				<div>
					<div style="float: left; margin-left: 3%;">
						<h4  v-if="error_message" style="color: red;">{{ error_message }}</h4>
					</div>
					<div class="row">
						<div class="col-lg-8 col-xl-8">
							<h5 style="padding-left: 5%;" v-if="conceptLabel">Concept: {{ conceptLabel }}</h5>
						</div>
						<div class="text-right col-lg-4 col-xl-4">
							<a v-if="allHidden()" v-on:click="showAll" class="btn">
								Show all
							</a>
							<a v-on:click="hideAll" class="btn">
								Hide all
							</a>
						</div>
					</div>
					<div>
						<div style="padding: 0%;" class="col-lg-12 col-xl-2" v-if="sidebar == 'submitAllAppellations'">
							<button v-bind:style="[calcSizeOfPage ? {float: 'right', 'margin-right': 3 + '%'} : {float: 'left', 'margin-left': 3 + '%'}]"   @click="deselectAllTemplatesRef()" class="btn btn-default btn-sm" v-tooltip="'Deselect All'"><span class="glyphicon glyphicon-remove-sign"></span></button>
							<button v-bind:style="[calcSizeOfPage ? {float: 'right', 'margin-right': 3 + '%'} : {float: 'left', 'margin-left': 3 + '%', 'margin-bottom': 3 + '%'}]"  @click="checkAll()" class="btn btn-default btn-sm" v-tooltip="'Select All'"><span class="glyphicon glyphicon-ok-sign"></span></button>
						</div>
						<div style="margin-bottom: 2%;" v-if="sidebar == 'submitAllAppellations'" >
							<div style="padding-right: 0%; padding-left: 0%; margin-left: 1%;" class="col-xl-6">
								<select class="btn btn-default dropdown-toggle"  v-if="sidebar == 'submitAllAppellations'" v-model="selected_template" style="float: left; margin-left: 2.5%; width: 100%;">
									<option value=0>Please select Relationship</option>
									<option v-for="template in templates" :value=template>{{ template.name }} - <span style="color: lightgrey;">{{ template.description }}</span></option>
								</select>
							</div>
							<div class="col-lg-12 col-xl-3" v-bind:style="[calcSizeOfPage ? {} : {'padding-left': 3.25 + '%'}]">
								<button v-if="!conceptLabel" v-bind:style="[calcSizeOfPage ? {'margin-top': 1 + '%'} : {'margin-top': 2 + '%', 'margin-bottom': 3 + '%'}]" @click="selectConcept()" class="btn btn-info btn-xs" >Select Text Concept</button>
							</div>
						</div>
						<div class="col-lg-12 col-xl-12" style="padding-left: 2.5%; padding-right: 1%">
							<ul class="list-group appellation-list" style="max-height: 400px; overflow-y: scroll; margin-top: 2%;">
								<appellation-list-item
									v-bind:sidebar="sidebar"
									v-on:hideappellation="hideAppellation"
									v-on:showappellation="showAppellation"
									v-on:selectappellation="selectAppellation"
									v-on:removeAppellation="removeAppellation($event)"
									v-on:addAppellation="addAppellation($event)"
									v-for="(appellation, index) in current_appellations"
									v-bind:appellation=appellation
									v-if="appellation != null"
									v-bind:index="index">
								</appellation-list-item>
							</ul>
						</div>
					</div>
				</div>
			   `,
    components: {
        'appellation-list-item': AppellationListItem,
    },
    data: function () {
        return {
            current_appellations: this.appellations,
            selected_template: null,
            templates: null,
            appellations_to_submit: [],
            error_message: "",
        }
    },
    computed: {
        conceptLabel: function () {
            return store.getters.conceptLabel
        },
        calcSizeOfPage: function () {
            let width = $(document).width();
            if (width >= 2000) {
                return true
            } else {
                return false
            }
        }
    },
    created: function () {
        this.getTemplates();
        store.commit('setAppellations', this.appellations);
        this.watchStoreForValidator();
    },
    watch: {
        appellations: function (value) {
            // Replace an array prop wholesale doesn't seem to trigger a
            //  DOM update in the v-for binding, but a push() does; so we'll
            //  just push the appellations that aren't already in the array.
            var current_ids = this.current_appellations.map(function (elem) {
                return elem.id;
            });
            var self = this;
            this.appellations.forEach(function (elem) {
                if (current_ids.indexOf(elem.id) < 0) {
                    self.current_appellations.push(elem);
                }
            });
        },
        selected_template: function () {
            store.commit("setTemplate", this.selected_template);
            if (store.getters.getValidator == 1) {
                store.commit('setValidator', 0)
            }
        },
    },
    methods: {
        /*************************************************
         * Start Methods to create relationships to text *
         *************************************************/
        selectConcept: function () {
            store.commit('triggerConcepts')
        },
        getTemplates: function () {
            RelationTemplateResource.get_single_relation().then(response => {
                this.templates = response.body;
            }).catch(function (error) {
                console.log('Failed to get relationtemplates', error);
            });
        },
        getTemplateFields: function () {
            RelationTemplateResource.query({
                search: this.selected_template,
                format: "json",
                all: false
            }).then(function (response) {
                store.commit("setTemplate", response.body.templates[0]);
            }).catch(function (error) {
                console.log('Failed to get relationtemplates', error);
                self.searching = false;
            });
        },
        deselectAllTemplatesRef: function () {
            store.commit('deselect');
        },
        checkAll: function () {
            store.commit('selectAll');
        },
        watchStoreForValidator: function () {
            store.watch(
                (state) => {
                    return store.getters.getValidator;
                },
                (val) => {
                    switch (val) {
                        case 0:
                            this.error_message = "";
                            break;
                        case 1:
                            this.error_message = "Please Select A Template";
                            break;
                        case 2:
                            this.error_message = "Please Select A Concept";
                            break;
                        case 3:
                            this.error_message = "Please Select At Least One Appellation";
                            break;
                    }
                },
            );
        },
        /***********************************************
         * End Methods to create relationships to text *
         ***********************************************/
        allHidden: function () {
            var ah = true;
            this.appellations.forEach(function (appellation) {
                if (appellation.visible) ah = false;
            });
            return ah;
        },
        hideAll: function () {
            this.$emit("hideallappellations");
        },
        showAll: function () {
            this.$emit("showallappellations");
        },
        hideAppellation: function (appellation) {
            this.$emit("hideappellation", appellation);
        },
        showAppellation: function (appellation) {
            this.$emit("showappellation", appellation);
        },
        selectAppellation: function (appellation) {
            this.$emit('selectappellation', appellation);
        },
    }
}