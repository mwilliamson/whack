import os
import subprocess


def create_gzipped_tarball_from_dir(source, destination):
    source_dir = os.path.dirname(source)
    source_name = os.path.basename(source)
    subprocess.check_call(["tar", "czf", destination, source_name], cwd=source_dir)

def extract_gzipped_tarball(source, destination, strip_components):
    subprocess.check_call([
        "tar", "xzf", source,
        "--directory", destination,
        "--strip-components", str(strip_components)
    ])
