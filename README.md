# PyLogger

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat\&logo=python\&logoColor=white)
![logging](https://img.shields.io/badge/logging-stdlib-blue?style=flat)
![Queue](https://img.shields.io/badge/queue-thread--safe-green?style=flat)
![License](https://img.shields.io/badge/license-MIT-brightgreen?style=flat)

|             |                                                        |
| ----------- | ------------------------------------------------------ |
| **Author**  | [Egor-Urban](https://github.com/Egor-Urban)            |
| **Version** | 2.7.16                                                 |
| **Stack**   | Python 3.10+, logging, Queue, TimedRotatingFileHandler |

---

## Description

**PyLogger** is a production-oriented logging module designed for reliability, performance, and clean output in Python applications.

It provides an asynchronous, queue-based logging pipeline with safe file rotation, colored console output, and graceful shutdown handling.

The design focuses on minimizing I/O blocking in the main thread while ensuring logs are consistently written to both console and disk.

### Key capabilities

* **Async logging pipeline** — built on `QueueHandler` + `QueueListener` to offload I/O from the main thread
* **Safe file rotation** — custom handler avoids common Linux file descriptor issues during log rotation
* **Colored console output** — improves readability during development and debugging
* **Path optimization** — cached relative paths reduce formatting overhead
* **Graceful shutdown** — integrates with `atexit`, `SIGINT`, and `SIGTERM`
* **Config-driven behavior** — all major parameters are controlled via `config.py`

---

## Project Structure

```
PyLogger/
│
├── logger.py          # Core logging module: setup, handlers, formatters
├── config.py          # Configuration (log paths, formats, rotation, levels)
```

### Key Components

**`setup_logging()`**
Entry point for initializing logging. Configures the root logger, creates the queue pipeline, and attaches handlers.

* Prevents duplicate initialization
* Creates log directory if missing
* Starts `QueueListener`
* Registers shutdown hooks

---

**`ColorFormatter`**
Extends the base formatter to add ANSI color codes for console output.

* Colors log levels (INFO, WARNING, ERROR, etc.)
* Highlights file paths
* Automatically disables colors if output is not a TTY

---

**`CachedRelativePathFormatter`**
Optimizes log formatting by caching relative file paths using `lru_cache`.

* Reduces repeated `os.path.relpath` calls
* Improves performance under high log throughput

---

**`LinuxSafeRotatingHandler`**
Custom implementation of `TimedRotatingFileHandler` with safer rollover behavior.

* Handles file conflicts during rotation
* Supports merge-on-conflict instead of overwrite
* Avoids common issues with open file descriptors on Linux

---

**Queue-based pipeline**

```
Application threads
        ↓
   QueueHandler
        ↓
      Queue
        ↓
   QueueListener
     ↙       ↘
Console    File
```

* Ensures non-blocking logging
* Centralizes all I/O in a single listener thread

---

## Configuration

All settings are controlled via `config.py`. Key parameters include:

* `LOG_DIRECTORY` — directory for log files
* `LOG_LEVEL` — root logging level
* `LOG_FORMAT` — log message format
* `LOG_DATETIME_FORMAT` — timestamp format
* `LOG_ROTATION_TIME` — rotation interval (e.g., `midnight`)
* `LOG_BACKUP_COUNT` — number of rotated files to keep
* `LOG_QUEUE_SIZE` — max queue size

---

## Usage

```python
from logger import setup_logging
import logging

setup_logging()

log = logging.getLogger(__name__)
log.info("Application started")
```

---

## Notes

* Designed primarily for Linux environments
* Safe to use in multi-threaded applications
* Does not require external dependencies
* Minimal overhead due to caching and async pipeline
