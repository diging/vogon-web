import json

class MockResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.text = content
        self.status_code = status_code

    @staticmethod
    def from_file(file_name):
        with open(file_name) as f:
            content = f.read()
            return MockResponse(content)

    def json(self):
        return json.loads(self.content)