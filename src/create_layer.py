import argparse
import json
import logging
import sys
import zipfile
from collections import Counter
from logging.config import fileConfig
from pathlib import Path
from time import sleep
from typing import Dict

import docker
import os
from docker.types import Mount


def _get_folder(folder_name: str) -> str:
    return os.path.join(Path(os.path.dirname(__file__)).parent, folder_name)


def _get_layer_full_name(layer_name: str, python_runtime: str, architecture: str) -> str:
    return f"{layer_name}_{python_runtime.replace('.', '_')}_{architecture}"


def _get_output_folder() -> str:
    return _get_folder("outputs")


def _build_layer(layer_name: str, lambda_base_image: str, architecture: str, skip_if_exists: bool) -> str:
    logging.info(f"Going to create layer: {layer_name}, Lambda base image: {lambda_base_image}")
    layer_file = f"{_get_layer_full_name(layer_name, lambda_base_image, architecture)}.zip"
    full_layer_file = os.path.join(_get_folder("outputs"), layer_file)
    if os.path.exists(full_layer_file):
        if skip_if_exists:
            logging.info("Layer file exists skipping creation")
            return full_layer_file
        else:
            os.remove(full_layer_file)
    layer_folder = _get_layer_folder(layer_name)
    logging.info(f"Source files for layer found under: {layer_folder}. Going to build layer file: {layer_file}")
    try:
        client = docker.from_env()
    except docker.errors.DockerException as e:
        logging.error(f"Failed to initialize Docker client: {e}")
        client = None
        exit(2)

    img, output = client.images.build(path=layer_folder, rm=True,
                                      dockerfile=os.path.join(os.path.dirname(__file__), "create_layer.Dockerfile"),
                                      quiet=False, nocache=False,
                                      buildargs={
                                          "LAYER_FILE": layer_file,
                                          "LAMBDA_BASE_IMAGE": lambda_base_image,
                                          "PLATFORM": _get_platform(architecture),
                                      })
    logging.info(f"Build result:\n{''.join([str(next(iter(row.values()))) for row in output])}")
    try:
        client.containers.run(image=img.id, remove=True,
                              mounts=[Mount(type="bind", source=_get_output_folder(), target="/outputs")])
    finally:
        sleep(3)
        img.remove()
    logging.info(f"Layer size: {_format_size(os.path.getsize(full_layer_file))}")
    return full_layer_file


def _get_layer_folder(layer_name: str) -> str:
    return os.path.join(_get_folder("layers"), layer_name)


def _get_platform(architecture: str):
    if architecture == "arm64":
        return "manylinux2014_aarch64"
    elif architecture == "x86_64":
        return "manylinux2014_x86_64"
    else:
        raise ValueError(f"Unknown architecture: {architecture}")


def _analyze_layer_file(layer_file: str, top_n: int):
    with zipfile.ZipFile(layer_file) as z:
        files_to_size = {f.filename: f.compress_size for f in z.infolist()}
    dirs: Dict[str, int] = {}
    for f, s in files_to_size.items():
        cur_dir = f.split("/")[1]
        if cur_dir not in dirs:
            dirs[cur_dir] = 0
        dirs[cur_dir] += s
    _log_dict("Dirs", dirs, top_n)
    _log_dict("Files", files_to_size, top_n)

    file_types: Dict[str, int] = {}
    for f, s in files_to_size.items():
        cur_ext = os.path.basename(f)
        if "." in cur_ext:
            cur_ext = cur_ext[cur_ext.rfind(".") + 1:]
        else:
            cur_ext = ""
        if cur_ext not in file_types:
            file_types[cur_ext] = 0
        file_types[cur_ext] += s
    _log_dict("File types", file_types, top_n)


def _log_dict(item_type: str, items: Dict, top_n: int):
    result = f"\n========== Top {top_n} {item_type} =========="
    for ext, size in Counter(items).most_common(top_n):
        if size > 0:
            result += f"\n{ext}, {_format_size(size)}"
    logging.info(result)


def _format_size(size: int) -> str:
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


def _publish_layer(layer_name: str, layer_file: str, python_runtime: str, architecture: str, bucket: str):
    import boto3
    layer_base_file_name = os.path.basename(layer_file)
    logging.info(f"Layer file name: {layer_base_file_name}, Layer size: {_format_size(os.path.getsize(layer_file))}")

    key = f"temp/{layer_base_file_name}"
    logging.info(f"Uploading to bucket: {bucket}. Key: {key}")
    session = boto3.session.Session()
    s3_client = session.client("s3")
    s3_client.upload_file(layer_file, bucket, key)
    try:
        layer_full_name = _get_layer_full_name(layer_name, python_runtime, architecture)
        logging.info(f"Creating Layer: {layer_name}")
        lambda_client = session.client("lambda")
        response = lambda_client.publish_layer_version(
            LayerName=layer_full_name,
            Content={
                'S3Bucket': bucket,
                'S3Key': key
            },
            CompatibleRuntimes=[f"python{python_runtime}"],
            CompatibleArchitectures=[architecture],
        )
    finally:
        s3_client.delete_object(Bucket=bucket, Key=key)
    if "Version" in response:
        logging.info(f"Layer version: {response['Version']}")
    else:
        logging.info(json.dumps(response, indent=4))


def run(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--layer", required=True, help="Layer name")
    parser.add_argument("-r", "--runtime", required=False, default="3.13", help="Python runtime")
    parser.add_argument("-a", "--architecture", required=False, default="x86_64", help="x86_64 or arm64")
    parser.add_argument("-s", "--skip", required=False, default="false",
                        help="Skip layer creation if layer already exists")
    parser.add_argument("-t", "--top", required=False, default=10,
                        help="Top item count in layer analysis. By default top 10 items are shown")
    parser.add_argument("-p", "--publish", required=False, default="false",
                        help="Publish lambda layer")
    parser.add_argument("-b", "--bucket", required=False,
                        help="S3 bucket to use, required for the publishing process")
    args = parser.parse_args(args=argv)

    if not os.path.exists(_get_layer_folder(args.layer)):
        logging.error(f"Layer folder does not exist: {args.layer}")
        exit(2)

    layer_file = _build_layer(args.layer, args.runtime, args.architecture,
                              args.skip.lower() == "true")
    _analyze_layer_file(layer_file, int(args.top))
    if args.publish.lower() == "true":
        if args.bucket is None:
            logging.error("Bucket must be provided for publishing")
            exit(2)
        _publish_layer(args.layer, layer_file, args.runtime, args.architecture, args.bucket)


if __name__ == '__main__':
    fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
    run(sys.argv[1:])
