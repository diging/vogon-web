var AppellationListItem = {
    props: ['appellation'],
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
                <div class="text-warning">{{ appellation.position.position_value }}</div>
               </li>`,
    watch: {
        appellation: function(appellation) {
            console.log('changed::', appellation);
        }
    },
    methods: {
        hide: function() { this.$emit("hideappellation", this.appellation); },
        show: function() { this.$emit("showappellation", this.appellation); },
        toggle: function() {
            if(this.appellation.visible) {
                this.hide();
            } else {
                this.show();
            }
        },
        isSelected: function() { return this.appellation.selected; },
        select: function() { this.$emit('selectappellation', this.appellation); },
        label: function() {
            if (this.appellation.interpretation) {
                return this.appellation.interpretation.label;
            } else if (this.appellation.dateRepresentation) {
                return this.appellation.dateRepresentation;
            }
        }
    }
}


AppellationList = {
    props: ['appellations'],
    template: `<ul class="list-group appellation-list" style="max-height: 400px; overflow-y: scroll;">
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
                       v-for="appellation in appellations"
                       v-if="appellation != null">
                   </appellation-list-item>
               </ul>`,
    components: {
        'appellation-list-item': AppellationListItem
    },
    methods: {
        allHidden: function() {
            var ah = true;
            this.appellations.forEach(function(appellation) {
                if (appellation.visible) ah = false;
            });
            return ah;
        },
        hideAll: function() { this.$emit("hideallappellations"); },
        showAll: function() { this.$emit("showallappellations"); },
        hideAppellation: function(appellation) { this.$emit("hideappellation", appellation); },
        showAppellation: function(appellation) { this.$emit("showappellation", appellation); },
        selectAppellation: function(appellation) { this.$emit('selectappellation', appellation); }
    }
}
