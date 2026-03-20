from nanobot.channels.whatsapp import WhatsAppChannel
from nanobot.config.schema import WhatsAppConfig
from nanobot.bus.queue import MessageBus

def test_whatsapp_default_deny_all():
    """Verify that WhatsApp default configuration denies access to everyone."""
    # Setup
    config = WhatsAppConfig() # Default config, allow_from is ["__explicit_allow_list_required__"]
    bus = MessageBus()
    channel = WhatsAppChannel(config, bus)

    # Test with a random sender
    sender_id = "1234567890"

    # Check if allowed
    is_allowed = channel.is_allowed(sender_id)

    print(f"Config allow_from: {config.allow_from}")
    print(f"Is sender {sender_id} allowed? {is_allowed}")

    # Assert that it IS NOT allowed (security fix verification)
    assert is_allowed == False, "Security Fix Failed: Sender should be denied by default"

    # Assert that the default list contains the sentinel value
    assert "__explicit_allow_list_required__" in config.allow_from

def test_whatsapp_explicit_allow():
    """Verify that WhatsApp allows access when explicitly configured."""
    # Setup
    config = WhatsAppConfig(allow_from=["1234567890"])
    bus = MessageBus()
    channel = WhatsAppChannel(config, bus)

    # Test with the allowed sender
    sender_id = "1234567890"
    is_allowed = channel.is_allowed(sender_id)
    assert is_allowed == True, "Explicit allow failed"

    # Test with another sender
    other_sender = "0987654321"
    is_allowed = channel.is_allowed(other_sender)
    assert is_allowed == False, "Explicit allow list should still deny others"

if __name__ == "__main__":
    test_whatsapp_default_deny_all()
    test_whatsapp_explicit_allow()
