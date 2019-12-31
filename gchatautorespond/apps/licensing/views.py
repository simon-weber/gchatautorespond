import logging

import braintree
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, render_to_response
from django.template.context_processors import csrf

from .lib import (
    transition_license,
    get_default_payment_method,
    report_bt_event,
    raise_unless_successful,
    UnsuccessfulResultError,
)

logger = logging.getLogger(__name__)


def handle_unsuccessful_result(view):
    def _result_wrapper(*args, **kwargs):
        try:
            return view(*args, **kwargs)
        except UnsuccessfulResultError as e:
            logger.exception("unsuccessful bt result from %s: %s", view, e.result)
            mail_admins("unsuccessful bt result", "See sentry for details.", fail_silently=True)
            return render_to_response('payment_error.html')

    return _result_wrapper


@login_required
@handle_unsuccessful_result
def details_view(request):
    if request.method == 'GET':
        license = request.user.currentlicense.license
        next_bill_date = trial_expire_date = None

        token_options = {}
        if license.bt_customer_id:
            token_options['customer_id'] = license.bt_customer_id
            token_options['options'] = {
                'make_default': True,
                'fail_on_duplicate_payment_method': False
            }

        client_token = braintree.ClientToken.generate(token_options)

        if license.bt_subscription_id:
            subscription = braintree.Subscription.find(license.bt_subscription_id)
            next_bill_date = subscription.next_billing_date
        if license.is_trial:
            trial_expire_date = license.trial_expire_date

        c = {
            'user': request.user,
            'client_token': client_token,
            'is_active': license.is_active,
            'has_valid_subscription': license.is_active and license.bt_subscription_id,
            'next_bill_date': next_bill_date,
            'trial_expire_date': trial_expire_date,
            'price': settings.PRICE_REPR,
            'admin_override': license.admin_override,
        }
        c.update(csrf(request))

        return render_to_response('details.html', c)
    elif request.method == 'POST':
        license = request.user.currentlicense.license
        if license.admin_override:
            logger.warning("attempt to change an overridden license %s", license)
            return redirect('license_details')

        nonce = request.POST['payment_method_nonce']

        if not license.bt_customer_id:
            result = braintree.Customer.create({
                'email': request.user.email,
                'payment_method_nonce': nonce,
                'first_name': request.user.username,
            })
            raise_unless_successful(result)
            report_bt_event(request.user.email, result, 'Customer', 'create')
            license = transition_license(license, {
                'bt_customer_id': result.customer.id,
            })
        else:
            result = braintree.PaymentMethod.create({
                'customer_id': license.bt_customer_id,
                'payment_method_nonce': nonce,
                'options': {'make_default': True},
            })
            raise_unless_successful(result)
            report_bt_event(request.user.email, result, 'PaymentMethod', 'create')

        customer = braintree.Customer.find(license.bt_customer_id)
        default_payment_method = get_default_payment_method(customer)
        if not license.bt_subscription_id:
            payload = {
                'plan_id': settings.PLAN_ID,
                'payment_method_token': default_payment_method.token,
            }
            if license.is_trial:
                payload['first_billing_date'] = license.trial_expire_date
            else:
                payload['options'] = {'start_immediately': True}

            result = braintree.Subscription.create(payload)
            raise_unless_successful(result)
            report_bt_event(request.user.email, result, 'Subscription', 'create')
            license = transition_license(license, {
                'bt_subscription_id': result.subscription.id,
                'bt_status': result.subscription.status,
            })
        else:
            result = braintree.Subscription.update(license.bt_subscription_id, {
                'payment_method_token': default_payment_method.token,
            })
            report_bt_event(request.user.email, result, 'Subscription', 'update')
            raise_unless_successful(result)
            license = transition_license(license, {
                'bt_status': result.subscription.status,
            })

        return redirect('license_details')
    else:
        return HttpResponseBadRequest()


@login_required
@handle_unsuccessful_result
def cancel_view(request):
    license = request.user.currentlicense.license
    can_cancel = bool(license.bt_subscription_id)
    if request.method == 'GET':
        inactive_date = None

        if can_cancel:
            subscription = braintree.Subscription.find(license.bt_subscription_id)
            inactive_date = max((license.trial_start + license.TRIAL_LENGTH).date(),
                                subscription.next_billing_date)

        c = {
            'user': request.user,
            'can_cancel': can_cancel,
            'inactive_date': inactive_date
        }
        c.update(csrf(request))

        return render_to_response('cancel.html', c)
    elif request.method == 'POST':
        if not can_cancel:
            return redirect('license_details')

        feedback = request.POST['feedback']

        result = braintree.Subscription.cancel(license.bt_subscription_id)
        raise_unless_successful(result)
        report_bt_event(request.user.email, result, 'Subscription', 'cancel')

        license = transition_license(license, {
            'bt_subscription_id': '',
            'bt_status': result.subscription.status,
        })

        mail_admins(
            "%s cancelled their subscription" %
            request.user.username,
            "Their feedback: %s" % feedback,
            fail_silently=True)

        return redirect('license_details')
    else:
        return HttpResponseBadRequest()
