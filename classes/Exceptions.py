class ApiException(Exception):
    def __init__(self, detail: str, status_code: int, headers: dict | None = None):
        self.detail = detail
        self.status_code = status_code
        self.headers = headers if headers is not None else dict()
