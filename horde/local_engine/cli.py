import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "horde.local_engine.server:app",
        host=os.getenv("HORDE_HOST", "127.0.0.1"),
        port=int(os.getenv("HORDE_PORT", "8787")),
        reload=False,
    )


if __name__ == "__main__":
    main()
