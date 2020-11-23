from django.db.migrations.operations.base import Operation


class AlterBaseOperation(Operation):
    reduce_to_sql = False
    reversible = True

    def __init__(self, model_name, bases, prev_bases):
        self.model_name = model_name
        self.bases = bases
        self.prev_bases = prev_bases

    def state_forwards(self, app_label, state):
        state.models[app_label, self.model_name].bases = self.bases
        state.reload_model(app_label, self.model_name)

    def state_backwards(self, app_label, state):
        state.models[app_label, self.model_name].bases = self.prev_bases
        state.reload_model(app_label, self.model_name)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def describe(self):
        return "Update %s bases to %s" % (self.model_name, self.bases)
