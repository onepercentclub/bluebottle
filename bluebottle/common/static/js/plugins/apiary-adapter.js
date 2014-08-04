if ('undefined' === typeof Apiary) {
    Apiary = {};

    if ('undefined' !== typeof window) {
        window.Apiary = Apiary;
    }
}

/*
 Apiary Adapter for Ember Data based off the DRF2 Adapter
 */

Apiary.MockSerializer = DS.DRF2Serializer.extend();

Apiary.MockAdapter = DS.DRF2Adapter.extend({
    serializer: Apiary.MockSerializer,

    // Optionally define plurals for each model.
    plurals: {},
});