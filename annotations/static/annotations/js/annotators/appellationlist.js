var AppellationListItem = {
    props: ['appellation'],
    template: `<li v-bind:class="{
                        'list-group-item': true,
                        'appellation-list-item': true,
                        'appellation-selected': isSelected()
                    }">
                <span class="pull-right text-muted btn-group">
                    <a v-if="!appellation.is_used" class="btn btn-xs" v-on:click="deleteAppellation()">
                        <span class="glyphicon glyphicon-trash"></span>
                    </a>
                    <a class="btn btn-xs" v-on:click="select">
                        <span class="glyphicon glyphicon-hand-down"></span>
                    </a>
                    <a class="btn btn-xs" v-on:click="toggle">
                        <span v-if="appellation.visible" class="glyphicon glyphicon glyphicon-eye-open"></span>
                        <span v-else class="glyphicon glyphicon glyphicon-eye-close"></span>
                    </a>
                </span>
                {{ label() }}
                <div class="text-warning">Created by <strong>{{ getCreatorName(appellation.createdBy) }}</strong> on {{ getFormattedDate(appellation.created) }}</div>
               </li>`,
    methods: {
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
        getFormattedDate: function (isodate) {
            var date = new Date(isodate);
            var monthNames = [
                "January", "February", "March",
                "April", "May", "June", "July",
                "August", "September", "October",
                "November", "December"
            ];
            var minutes = String(date.getMinutes());
            if (minutes.length == 1) {
                minutes = '0' + minutes;
            }

            var day = date.getDate();
            var monthIndex = date.getMonth();
            var year = date.getFullYear();

            return day + ' ' + monthNames[monthIndex] + ', ' + year + ' at ' + date.getHours() + ':' + minutes;
        },
        getCreatorName: function (creator) {
            if (creator.id == USER_ID) {
                return 'you';
            } else {
                return creator.username;
            }
        },
        deleteAppellation() {
            Appellation.delete({
                id: this.appellation.id
            }).then(response => {
                let i = store.getters.getAppellationsToSubmit.length;
                /* 
                * Remove appellations that have the string represenation that matches the text title
                * this assumes the appellation is that of the text and we remove it as to not make a
                * relation to itself. You must iterate backwards when removing items from an array to
                * prevent indexing errors.
                */
                while (i) {
                    try {
                        if (store.getters.getAppellationsToSubmit[i].stringRep == this.text.title) {
                            store.commit('removeAppellation', i);
                        }
                    } catch (error) {

                    }
                    i--;
                }
                    console.log(response);
            }, response => {
                // error callback
            });
        }
    }
}


AppellationList = {
    props: ['appellations'],
    template: `
            <div>
                <ul class="list-group appellation-list" style="max-height: 400px; overflow-y: scroll;">
                    <div class="text-right">
                        <a v-if="allHidden()" v-on:click="showAll" class="btn">
                            Show all
                        </a>
                            <a v-on:click="hideAll" class="btn">
                                Hide all
                            </a>
                    </div>
                    <appellation-list-item
                        v-on:hideappellation="hideAppellation"
                        v-on:showappellation="showAppellation"
                        v-on:selectappellation="selectAppellation"
                        v-bind:appellation=appellation
                        v-for="appellation in current_appellations"
                        v-if="appellation != null">
                    </appellation-list-item>
                </ul>
            </div>`,
    components: {
        'appellation-list-item': AppellationListItem
    },
    data: function () {
        return {
            current_appellations: this.appellations,
            loading: true
        }
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
        }
    },
    methods: {
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
        }
    }
}