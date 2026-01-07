class VectorStore:
    def __init__(self, path: str):
        self.path = path

    def add(self, id: str, embedding):
        pass

    def query(self, embedding, top_k: int = 3):
        return []
