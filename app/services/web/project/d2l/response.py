# from datetime import datetime, timedelta

class Response:
    def __init__(self, original) -> None:
        self.original = original
        output = self.original.content.decode()
        if output:
            if 'application/json' in self.original.headers.get('Content-Type', ''):
                self.data = self.original.json()
            else:
                self.data = output
        else:
            self.data = ''

    def __repr__(self) -> str:
        return '<Response [{self.status_code}]>'

    @property
    def status_code(self):
        return self.original.status_code

    # @property
    # def throttling(self) -> datetime:
    #     """throttling

    #     Returns:
    #         datetime: Retry after.
    #     """
    #     if "Retry-After" in self.original.headers:
    #         return datetime.now() + timedelta(seconds=self.original.headers["Retry-After"])
    #     return None
