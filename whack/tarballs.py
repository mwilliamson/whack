import os
import shutil

import requests

from .files import mkdir_p
from .tempdir import create_temporary_dir
from . import local
from .uris import is_http_uri


def extract_tarball(tarball_uri, destination_dir, strip_components):
    if is_http_uri(tarball_uri):
        with create_temporary_dir() as temp_dir:
            tarball_path = _download_tarball(tarball_uri, temp_dir)
            extract_tarball(tarball_path, destination_dir, strip_components)
    else:
        mkdir_p(destination_dir)
        local.run([
            "tar", "xzf", tarball_uri,
            "--directory", destination_dir,
            "--strip-components", str(strip_components)
        ])


def _download_tarball(url, tarball_dir):
    tarball_path = os.path.join(tarball_dir, "tarball.tar.gz")
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise Exception("Status code was: {0}".format(response.status_code))
    with open(tarball_path, "wb") as tarball_file:
        shutil.copyfileobj(response.raw, tarball_file)
    return tarball_path


def create_tarball(tarball_path, source, rename_dir=None):
    args = [
        "tar", "czf", tarball_path,
        "--directory", os.path.dirname(source),
        os.path.basename(source)
    ]
    if rename_dir is not None:
        args += [
            "--transform",
            "s/^{0}/{1}/".format(os.path.basename(source), rename_dir),
        ]
    local.run(args)
    return tarball_path
