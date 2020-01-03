import stripe


def create_mock_intent():
    intent = stripe.PaymentIntent('some intent id')
    stripe_charge = stripe.Charge()
    stripe_payment_method = stripe.PaymentMethod()
    stripe_payment_method.update({'type': 'visa'})
    stripe_charge.update({
        'payment_method_details': stripe_payment_method
    })
    list_object = stripe.ListObject()
    list_object['data'] = [stripe_charge]
    intent.update({
        'client_secret': 'some client secret',
        'charges': list_object
    })
    return intent
