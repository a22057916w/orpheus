class Track:
    """Represents a music track."""

    def __init__(
        self,
        title: str,
        author: str,
        url: str,
        duration: int,
        thumbnail: str = None,
        stream_url: str = None,
    ):
        self.title = title
        self.author = author
        # Canonical page URL (e.g. the YouTube watch URL). Empty for tracks that came from
        # Spotify, which are matched against YouTube by title/author when they are played.
        self.url = url
        self.duration = duration
        self.thumbnail = thumbnail
        # Direct audio URL handed to FFmpeg. These expire and are tied to the session that
        # extracted them, so it is resolved right before playback rather than at queue time.
        self.stream_url = stream_url

    def __str__(self) -> str:
        return f"{self.title} by {self.author}"

    @property
    def search_query(self) -> str:
        return f"{self.title} {self.author}".strip()
