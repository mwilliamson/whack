import subprocess

from .files import mkdir_p


def extract_tarball(tarball_path, destination_dir, strip_components):
        mkdir_p(destination_dir)
        subprocess.check_call([
            "tar", "xzf", tarball_path,
            "--directory", destination_dir,
            "--strip-components", str(strip_components)
        ])
