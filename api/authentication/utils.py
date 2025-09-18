import json, base64, logging

logger = logging.getLogger(__name__)

def encode_state(tenant, allauth_state):
    custom_state = {
        "tenant": tenant,
        "allauth": allauth_state,
    }
    encoded = base64.urlsafe_b64encode(json.dumps(custom_state).encode()).decode()
    logger.debug("[STATE ENCODE] tenant=%s allauth=%s encoded=%s", tenant, allauth_state, encoded)
    return encoded

def decode_state(state):
    try:
        decoded = json.loads(base64.urlsafe_b64decode(state))
        tenant = decoded.get("tenant")
        allauth_state = decoded.get("allauth")
        logger.debug("[STATE DECODE] raw=%s tenant=%s allauth=%s", state, tenant, allauth_state)
        return tenant, allauth_state
    except Exception as e:
        logger.error("[STATE ERROR] failed to decode state=%s error=%s", state, e)
        return None, state
