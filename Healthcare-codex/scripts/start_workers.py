"""Start all pipeline workers and keep them running."""
import logging
import signal
import sys
import time

from db.database import init_db
from workers.parser_worker import ParserWorker
from workers.markdown_worker import MarkdownWorker
from workers.chunking_worker import ChunkingWorker
from workers.pii_worker import PiiWorker
from workers.embedding_worker import EmbeddingWorker
from workers.keyword_index_worker import KeywordIndexWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Initialising database...")
    init_db()

    workers = [
        ParserWorker(),
        MarkdownWorker(),
        ChunkingWorker(),
        PiiWorker(),
        EmbeddingWorker(),
        KeywordIndexWorker(),
    ]

    for w in workers:
        w.start()
    logger.info("All %d workers started", len(workers))

    def _shutdown(sig, frame):
        logger.info("Shutting down workers...")
        for w in workers:
            w.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        _shutdown(None, None)


if __name__ == "__main__":
    main()
