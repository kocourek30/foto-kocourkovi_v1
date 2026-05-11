import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.orders.models import GalleryOrder

logger = logging.getLogger(__name__)


def _brand_name() -> str:
    return getattr(settings, "SITE_BRAND_NAME", "Foto Kocourkovi")


def _client_contact_label(order: GalleryOrder) -> str:
    if order.customer_email:
        return f"E-mail: {order.customer_email}"
    full_name = f"{order.customer_first_name} {order.customer_last_name}".strip()
    if full_name:
        return f"Jméno: {full_name}"
    return "Kontakt neuveden"


def _client_greeting(order: GalleryOrder) -> str:
    if order.customer_first_name:
        return f"Dobrý den, {order.customer_first_name},"
    return "Dobrý den,"


def _build_context(order: GalleryOrder) -> dict:
    return {
        "brand_name": _brand_name(),
        "order": order,
        "gallery_title": order.gallery.title,
        "job_title": order.gallery.job.title if order.gallery_id else "",
        "items_count": order.items_count,
        "total_price": order.total_price,
        "client_contact": _client_contact_label(order),
        "client_greeting": _client_greeting(order),
    }


def _send_email_with_html(subject: str, text_body: str, html_template: str, context: dict, to: list[str]) -> None:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost")
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=to,
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)


def send_order_submitted_notifications(order: GalleryOrder) -> None:
    notification_email = getattr(settings, "ORDER_NOTIFICATION_EMAIL", "").strip()
    brand_name = _brand_name()
    context = _build_context(order)

    if notification_email:
        subject = f"Nová objednávka – {order.gallery.title} ({order.public_id})"
        text_body = (
            f"Byla vytvořena nová objednávka přes galerii {order.gallery.title}.\n\n"
            f"Reference: {order.public_id}\n"
            f"Galerie: {order.gallery.title}\n"
            f"Zakázka: {order.gallery.job.title}\n"
            f"Položky: {order.items_count}\n"
            f"Celkem: {order.total_price} Kč\n"
            f"{_client_contact_label(order)}\n\n"
            f"Objednávku najdete v administraci {brand_name}."
        )
        try:
            _send_email_with_html(
                subject=subject,
                text_body=text_body,
                html_template="orders/email/order_submitted_internal.html",
                context=context,
                to=[notification_email],
            )
        except Exception:
            logger.exception(
                "Nepodařilo se odeslat interní notifikaci pro objednávku %s.",
                order.public_id,
            )

    if order.customer_email:
        subject = f"Potvrzení objednávky – {brand_name} ({order.public_id})"
        text_body = (
            f"{_client_greeting(order)}\n\n"
            f"děkujeme za vaši objednávku v galerii {order.gallery.title}.\n\n"
            f"Reference: {order.public_id}\n"
            f"Položky: {order.items_count}\n"
            f"Celkem: {order.total_price} Kč\n\n"
            "Objednávku nyní zpracujeme. V případě potřeby se vám ozveme s dalším postupem.\n\n"
            f"S pozdravem,\n{brand_name}"
        )
        try:
            _send_email_with_html(
                subject=subject,
                text_body=text_body,
                html_template="orders/email/order_submitted_client.html",
                context=context,
                to=[order.customer_email],
            )
        except Exception:
            logger.exception(
                "Nepodařilo se odeslat potvrzení klientovi pro objednávku %s.",
                order.public_id,
            )
