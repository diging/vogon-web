// Be gone event buses. The store should be used instead instead of event buses
const store = new Vuex.Store({
    state: {
        show_concepts: false,
        concept_label: "",
        template: null
    },
    mutations: {
        triggerConcepts(state, payload) {
            /*
             * Need if in order for cancel button to work when 
             * conecpt picker is triggered by highlighting a word
             */
            if(payload == false){
                state.show_concepts = payload
            } else {
                state.show_concepts = !state.show_concepts;
            }
            
        },
        conceptLabel(state, payload) {
            state.concept_label = payload
        },
        setTemplate(state, payload) {
            state.template = payload
        }
    },
    getters: {
        showConcepts: state => state.show_concepts,
        conceptLabel: state => state.concept_label,
        getTemplate: state => state.template,
    }
})