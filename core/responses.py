from datetime import datetime, timezone
from drf_spectacular.utils import OpenApiExample

def build_response(*, success:bool, code:int, message:str, data:dict|None=None):
    return {
        "success" : success,
        "code" : code,
        "message" : message,
        "timestamp" : datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "data" : data or {}
    }

def swagger_response(*, name, success, code, message, data=None):
    return OpenApiExample(
        name = name,
        value = build_response(
            success = success,
            code = code,
            message = message,
            data = data
        ),
        response_only = True,
        media_type = "application/json",
    )