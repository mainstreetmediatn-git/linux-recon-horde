import subprocess
from pathlib import Path
from typing import Tuple


class ExecutionEngine:
    @staticmethod
    def run_process(
        executable: str,
        args: list[str],
        target: str,
        stdout_path: Path,
        stderr_path: Path,
    ) -> Tuple[int, subprocess.Popen]:
        formatted_args = [arg.format(target=target) for arg in args]
        cmd_array = [executable, *formatted_args]

        stdout_file = open(stdout_path, "w", encoding="utf-8")
        stderr_file = open(stderr_path, "w", encoding="utf-8")
        try:
            process = subprocess.Popen(
                cmd_array,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                shell=False,
                start_new_session=True,
            )
        finally:
            stdout_file.close()
            stderr_file.close()

        return process.pid, process
