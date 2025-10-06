# services/chatbot_logic.py
def generate_auto_reply(message_text):
    """
    Simple example — could integrate with an LLM or rule-based logic.
    """
    if "price" in message_text.lower():
        return "Thank you for your inquiry! Our prices start at $50. Would you like a brochure?"
    elif "hello" in message_text.lower():
        return "Hello! How can we help your business today?"
    else:
        return "Thanks for reaching out. We'll get back to you soon."
