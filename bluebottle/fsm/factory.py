from factory import DjangoModelFactory


class FSMModelFactory(DjangoModelFactory):

    @classmethod
    def create(cls, as_user=None, as_relation=None, **kwargs):
        if as_user:
            model = super(FSMModelFactory, cls).build(**kwargs)
            model.execute_triggers(user=as_user)
            model.save()
            return model
        if as_relation:
            model = super(FSMModelFactory, cls).build(**kwargs)
            model.execute_triggers(user=getattr(model, as_relation))
            model.save()
            return model

        return super(FSMModelFactory, cls).create(**kwargs)

    @classmethod
    def create_batch(cls, size, as_user=None, as_relation=None, **kwargs):
        if as_user:
            batch = super(FSMModelFactory, cls).build_batch(size, **kwargs)
            for model in batch:
                model.execute_triggers(user=as_user)
                model.save()
            return batch
        if as_relation:
            batch = super(FSMModelFactory, cls).build_batch(size, **kwargs)
            for model in batch:
                model.execute_triggers(user=getattr(model, as_relation))
                model.save()
            return batch
        return super(FSMModelFactory, cls).create_batch(size, **kwargs)
