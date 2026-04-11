class Track:
    """Represents a music track."""

    def __init__(self, title: str, author: str, url: str, duration: int, thumbnail: str = None):
        self.title = title
        self.author = author
        self.url = url
        self.duration = duration
        self.thumbnail = thumbnail

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    @property
    def search_query(self) -> str:
        return f"{self.title} {self.author}".strip()
