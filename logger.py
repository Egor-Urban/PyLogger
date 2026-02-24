# ./logger.py

# Developer: Urban Egor
# Version: 2.7.16 r



import logging
import os
import sys
import time
import shutil
import atexit
import signal
from logging.handlers import TimedRotatingFileHandler, QueueHandler, QueueListener
from queue import Queue
from functools import lru_cache
from typing import Optional

import config



@lru_cache(maxsize=256)
def get_cached_relpath(pathname: str) -> str:
    try:
        return os.path.relpath(pathname)
        
    except (ValueError, Exception):
        return pathname



class CachedRelativePathFormatter(logging.Formatter):
    def format(self, record):
        if not hasattr(record, 'relpath'):
            record.relpath = get_cached_relpath(record.pathname)

        return super().format(record)



class ColorFormatter(CachedRelativePathFormatter):   
    def __init__(self, fmt, datefmt=None):
        super().__init__(fmt, datefmt)
        self.use_colors = sys.stdout.isatty() or os.getenv("FORCE_COLOR") == "1" 
        
    LEVEL_COLORS = {
        logging.DEBUG: "\x1b[38;20m",    # Grey
        logging.INFO: "\x1b[34;20m",     # Blue
        logging.WARNING: "\x1b[33;20m",  # Yellow
        logging.ERROR: "\x1b[31;20m",    # Red
        logging.CRITICAL: "\x1b[31;1m",  # Bold Red
    }

    CYAN = "\x1b[36m"
    RESET = "\x1b[0m"


    def format(self, record):
        if not hasattr(record, 'relpath'):
            record.relpath = get_cached_relpath(record.pathname)
            
        if not self.use_colors:
            return super().format(record)

        orig_levelname = record.levelname
        orig_relpath = record.relpath

        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{orig_levelname}{self.RESET}"
        record.relpath = f"{self.CYAN}{orig_relpath}{self.RESET}"

        try:
            return super().format(record)
        
        finally:
            record.levelname = orig_levelname
            record.relpath = orig_relpath



class LinuxSafeRotatingHandler(TimedRotatingFileHandler):
    def handleError(self, record):
        sys.stderr.write(f"--- LOGGER CRITICAL ERROR: {record} ---\n")
        super().handleError(record)


    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        dfn = os.path.join(
            os.path.dirname(self.baseFilename), 
            time.strftime(getattr(config, 'LOG_FILENAME_FORMAT', '%Y-%m-%d_%H-%M-%S.log'))
        )

        if os.path.exists(self.baseFilename):
            try:
                if os.path.exists(dfn):
                    with open(self.baseFilename, 'rb') as f_in, open(dfn, 'ab') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    os.remove(self.baseFilename)

                else:
                    os.rename(self.baseFilename, dfn)

            except (OSError, IOError):
                self.handleError(None)
        
        if not self.delay:
            self.stream = self._open()



def setup_logging() -> Optional[QueueListener]:
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return None

    log_dir = getattr(config, 'LOG_DIRECTORY', 'logs')
    os.makedirs(log_dir, mode=0o755, exist_ok=True)

    log_queue = Queue(getattr(config, 'LOG_QUEUE_SIZE', 10000))
    
    log_format = getattr(config, 'LOG_FORMAT', '[%(asctime)s] %(levelname)-8s [%(relpath)s:%(lineno)d] %(message)s')
    date_format = getattr(config, 'LOG_DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(ColorFormatter(log_format, datefmt=date_format))

    file_path = os.path.join(log_dir, getattr(config, 'LOG_CURRENT_NAME', 'current.log'))
    file_h = LinuxSafeRotatingHandler(
        filename=file_path,
        when=getattr(config, 'LOG_ROTATION_TIME', 'midnight'),
        backupCount=getattr(config, 'LOG_BACKUP_COUNT', 7),
        encoding=getattr(config, 'ENCODING', 'utf-8')
    )

    file_h.setFormatter(CachedRelativePathFormatter(log_format, datefmt=date_format))

    listener = QueueListener(log_queue, console_h, file_h, respect_handler_level=True)
    listener.start()

    def stop_all(*args):
        listener.stop()
        if args and isinstance(args[0], int):
            sys.exit(0)

    atexit.register(stop_all)
    signal.signal(signal.SIGTERM, stop_all)
    signal.signal(signal.SIGINT, stop_all)

    root_logger.setLevel(getattr(config, 'LOG_LEVEL', logging.INFO))
    root_logger.addHandler(QueueHandler(log_queue))
    
    return listener
