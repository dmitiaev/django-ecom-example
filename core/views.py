import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, View
import yookassa

from .forms import CheckoutForm
from .models import Item, Order, OrderItem, CheckoutAddress, Payment


# Create your views here.
class HomeView(ListView):
    model = Item
    template_name = "home.html"


class ProductView(DetailView):
    model = Item
    template_name = "product.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an order")
            return redirect("/")


class CheckoutView(View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {"form": form, "order": order}
        return render(self.request, "checkout.html", context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get("street_address")
                apartment_address = form.cleaned_data.get("apartment_address")
                country = form.cleaned_data.get("country")
                zip = form.cleaned_data.get("zip")
                # TODO: add functionaly for these fields
                # same_billing_address = form.cleaned_data.get('same_billing_address')
                # save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get("payment_option")

                checkout_address = CheckoutAddress(
                    user=self.request.user,
                    street_address=street_address,
                    apartment_address=apartment_address,
                    country=country,
                    zip=zip,
                )
                checkout_address.save()
                order.checkout_address = checkout_address
                order.save()

                return redirect("core:payment", payment_option="stripe")

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an order")
            return redirect("core:order-summary")


class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {"order": order}
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)

        idempotence_key = str(uuid.uuid4())
        payload = order.to_yookassa_payload()
        yookassa_payment = yookassa.Payment.create(payload, idempotence_key)

        # create payment
        payment = Payment()
        payment.stripe_id = yookassa_payment.id
        payment.user = self.request.user
        payment.amount = int(float(payload['amount']['value']))
        payment.save()

        # assign payment to order
        order.ordered = True
        order.payment = payment
        order.save()

        messages.success(self.request, "Success make an order")
        return redirect(yookassa_payment.confirmation.confirmation_url)


@method_decorator(csrf_exempt, name='dispatch')
class NotificationView(View):
    def post(self, *args, **kwargs):
        print(self.request.body)
        return HttpResponse(status=200)

    def get(self):
        print("Hello, World!")
        return redirect("/")

@login_required
def add_to_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]

        order_item, created = OrderItem.objects.get_or_create(
            item=item, order__pk=order.id, user=request.user
        )

        if order.items.filter(item__pk=item.pk, order__pk=order.id).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "Added quantity Item")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Item added to your cart")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order_item = OrderItem.objects.create(
            item=item, user=request.user, order=order
        )

        order.items.add(order_item)
        messages.info(request, "Item added to your cart")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            order_item.delete()
            messages.info(
                request,
                'Item "' + order_item.item.item_name + '" remove from your cart',
            )
            return redirect("core:order-summary")
        else:
            messages.info(request, "This Item not in your cart")
            return redirect("core:product", pk=pk)
    else:
        # add message doesnt have order
        messages.info(request, "You do not have an Order")
        return redirect("core:product", pk=pk)


@login_required
def reduce_quantity_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__pk=item.pk).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order_item.delete()
            messages.info(request, "Item quantity was updated")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This Item not in your cart")
            return redirect("core:order-summary")
    else:
        # add message doesnt have order
        messages.info(request, "You do not have an Order")
        return redirect("core:order-summary")
