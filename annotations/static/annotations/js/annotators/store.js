// Be gone event buses. The store should be used instead instead of event buses
const store = new Vuex.Store({
    state: {
        show_concepts: false
    },
    mutations: {
        triggerConcepts(state) {
            state.show_concepts = !state.show_concepts;
        }
    },
    getters: {
        show_concepts: state => state.show_concepts,
    }
})