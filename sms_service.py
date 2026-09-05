"""
SMS stub for Reflex.

In production this would call a real SMS gateway (e.g. Africa's Talking)
to actually send a text message to a customer or retailer. For this
sprint, it's a stub: it does not send a real message, it just logs
what WOULD have been sent.

This lets the rest of the app (assign_delivery, qr_confirm_delivery)
call send_sms() today exactly the way it would call a real gateway,
so swapping in the real integration later means changing only this
file, not any of the routes that use it.
"""


def send_sms(phone_number, message):
    """
    Stub SMS sender.

    Args:
        phone_number: the recipient's phone number (string)
        message: the text to send (string)

    Returns:
        A dict describing what was "sent" - useful for logging/testing.
    """
    print(f"[SMS STUB] To: {phone_number} | Message: {message}")

    return {
        "status": "stubbed",
        "to": phone_number,
        "message": message
    }
