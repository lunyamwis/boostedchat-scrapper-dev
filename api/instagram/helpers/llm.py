import logging
import os

import requests


def query_gpt(prompt):
    body = {
        "model": "gpt-4-1106-preview",
        "response_format":{"type":"json_object"},
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY").strip()}

    res = requests.post("https://api.openai.com/v1/chat/completions", json=body, headers=header)
    logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))
    # logging.warn('\nmodel API response', str(res.json()))
    return res.json()
