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