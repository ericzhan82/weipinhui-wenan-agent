import logging

from app.runtime import initialize_runtime
from app.services.copy_batch_service import run_copy_batch_workers_forever


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def main() -> None:
    initialize_runtime(recover_batches=True)
    run_copy_batch_workers_forever()


if __name__ == "__main__":
    main()
