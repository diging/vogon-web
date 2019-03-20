RelationListItem = {
    props: ['relation'],
    template: `<li v-bind:class="{
                        'list-group-item': true,
                        'relation-list-item': true,
                        'relation-selected': isSelected()
                    }">
                    <span class="pull-right text-muted btn-group">
                        <a class="btn btn-xs" v-on:click="select">
                            <span class="glyphicon glyphicon-hand-down"></span>
                        </a>
                    </span>
                    <div>{{ getRepresentation(relation) }}</div>
                    <div class="text-warning">Created by <strong>{{ getCreatorName(relation.createdBy) }}</strong> on {{ getFormattedDate(relation.created) }}</div>
                </li>`,

    methods: {
        select: function () {
            this.$emit('selectrelation', this.relation);
        },
        isSelected: function () {
            return this.relation.selected;
        },
        getRepresentation: function (relation) {
            if (relation.representation) {
                return relation.representation;
            } else {
                return relation.appellations.map(function (appellation) {
                    return appellation.interpretation.label;
                }).join('; ');
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
        }
    }
}

RelationList = {
    props: ['relations'],
    template: `<ul class="list-group relation-list">
                   <relation-list-item
                       v-on:selectrelation="selectRelation"
                       v-bind:relation=relation
                       v-for="relation in relations">
                   </relation-list-item>
               </ul>`,
    components: {
        'relation-list-item': RelationListItem
    },
    methods: {
        selectRelation: function (relation) {
            this.$emit('selectrelation', relation);
        }
    }
}