from datetime import datetime
import inspect
import os
import threading
import queue



def get_path():
    frame = inspect.currentframe().f_back  
    filename = os.path.basename(frame.f_code.co_filename)
    func_name = frame.f_code.co_name

    cls_name = None
    if 'self' in frame.f_locals:
        cls_name = frame.f_locals['self'].__class__.__name__

    if cls_name:
        return f"{filename}:{cls_name}/{func_name}"
    else:
        return f"{filename}:{func_name}"



class Log:
    def __init__(self):
        self.log_dir = "logs"
        os.makedirs(self.log_dir, exist_ok=True)

        self.date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        self.filename = os.path.join(
            self.log_dir, datetime.now().strftime("%d.%m.%Y") + ".log"
        )

        self.queue = queue.Queue()
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._writer, daemon=True)
        self.thread.start()


    def _writer(self):
        with open(self.filename, "a", encoding="utf-8") as f:
            while not self._stop_event.is_set() or not self.queue.empty():
                try:
                    line = self.queue.get(timeout=0.2)
                    f.write(line + "\n")
                    f.flush()
                except queue.Empty:
                    continue


    def _log(self, level, msg, extra=""):
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        entry = f"[{timestamp}][{get_path()}][{level}]{extra} {msg}"
        print(entry)
        self.queue.put(entry)


    def info(self, msg):
        self._log("INFO", msg)


    def warn(self, msg):
        self._log("WARNING", msg)


    def error(self, msg, is_fatal=False):
        if is_fatal:
            self._log("ERROR", msg, "[FATAL]")
        else:
            self._log("ERROR", msg)


    def debug(self, msg):
        self._log("DEBUG", msg)


    def close(self):
        self._stop_event.set()
        self.thread.join()



# TEST
if __name__ == "__main__":
    log = Log()
    log.info("Info test")
    log.debug("Debug test")
    log.warn("Warning test!")
    log.error("Fatal error test!", is_fatal=True)
    log.error("Error test")

    log.close()
