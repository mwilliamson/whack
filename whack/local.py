import spur


__all__ = ["run", "RunProcessError"]


local_shell = spur.LocalShell()

run = local_shell.run

RunProcessError = spur.RunProcessError
