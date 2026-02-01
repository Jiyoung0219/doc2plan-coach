import os
import json
import base64
import requests

DOC_PARSE_URL = "https://api.upstage.ai/v1/document-ai/document-parse"
IE_EXTRACT_URL = "https://api.upstage.ai/v1/document-ai/information-extract"
SOLAR_CHAT_URL = "https://api.upstage.ai/v1/solar/chat/completions"
CHAT_URL       = "https://api.upstage.ai/v1/chat/completions"


class UpstageClient:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise RuntimeError("UPSTAGE_API_KEY is missing. Put it in .env")
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def document_parse(self, file_bytes: bytes, filename: str):
        files = {"document": (filename, file_bytes)}
        r = requests.post(DOC_PARSE_URL, headers=self.headers, files=files, timeout=120)
        r.raise_for_status()
        return r.json()

    def information_extract(self, file_bytes: bytes, filename: str, schema: dict, mode: str = "enhanced"):
        # 파일을 base64로 인코딩
        b64 = base64.b64encode(file_bytes).decode("utf-8")

        # 티스토리 예시처럼 application/octet-stream으로 두는 게 가장 무난함 :contentReference[oaicite:1]{index=1}
        data_url = f"data:application/octet-stream;base64,{b64}"

        payload = {
            "model": "information-extract",  # ✅ alias 사용 (가장 안정) :contentReference[oaicite:2]{index=2}
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}}
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "document_schema",
                    "schema": schema
                }
            },
            # 티스토리 예시의 extra_body 옵션 :contentReference[oaicite:3]{index=3}
            "extra_body": {
                "mode": mode,          # "standard" / "enhanced"
                "location": False,     # 필요하면 True
                "confidence": False    # 필요하면 True
            }
        }

        r = requests.post(
            SOLAR_CHAT_URL,  # ✅ https://api.upstage.ai/v1/solar/chat/completions
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=180,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"IE Error {r.status_code}: {r.text}")
        return r.json()

            
        


    def solar_chat(self, system: str, user: str, model: str = "solar-pro"):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
        }
        r = requests.post(
            SOLAR_CHAT_URL,
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"SOLAR Error {r.status_code}: {r.text}")
        return r.json()

def extract_text_from_solar_response(resp: dict) -> str:
    try:
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(resp, ensure_ascii=False, indent=2)

def extract_text_from_ie_response(resp: dict) -> str:
    try:
        return resp["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(resp, ensure_ascii=False, indent=2)
