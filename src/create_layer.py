import argparse
import json
import logging
import sys
import zipfile
from logging.config import fileConfig
from pathlib import Path
from time import sleep
from typing import Dict, Optional

import docker
import os
from docker.types import Mount


def _get_folder(folder_name: str) -> str:
    return os.path.join(Path(os.path.dirname(__file__)).parent, folder_name)


def _get_dockerfile() -> str:
    return os.path.join(os.path.dirname(__file__), "create_layer.Dockerfile")


def get_layer_folder(layer_name: str, layer_version: str = None) -> str:
    folder = os.path.join(_get_folder("layers"), layer_name)
    if layer_version is not None:
        folder = os.path.join(folder, layer_version)
    return folder


def get_layer_output_file(layer_name: str, layer_version: Optional[str]) -> str:
    if layer_version is None:
        layer_version = "latest"
    return f"{layer_name}_{layer_version}.zip"


def get_output_folder() -> str:
    return _get_folder("outputs")


def create_layer(layer_name: str, layer_version: Optional[str], lambda_base_image: str) -> str:
    logging.info(f"Going to create layer: {layer_name}, Version: {layer_version}, Lambda base image: {lambda_base_image}")
    layer_file = get_layer_output_file(layer_name, layer_version)
    full_layer_file = os.path.join(get_output_folder(), layer_file)
    if os.path.exists(full_layer_file):
        os.remove(full_layer_file)
    layer_folder = get_layer_folder(layer_name, layer_version)
    logging.info(f"Source files for layer found under: {layer_folder}. Going to build layer file: {layer_file}")
    client = docker.from_env()
    img, output = client.images.build(path=layer_folder, rm=True,
                                      dockerfile=_get_dockerfile(),
                                      quiet=False, nocache=False,
                                      buildargs={
                                          "LAYER_FILE": layer_file,
                                          "LAMBDA_BASE_IMAGE": lambda_base_image,
                                      })
    logging.info(f"Build result:\n{''.join([str(next(iter(row.values()))) for row in output])}")
    try:
        client.containers.run(image=img.id, remove=True,
                              mounts=[Mount(type="bind", source=get_output_folder(), target="/outputs")])
    finally:
        sleep(3)
        img.remove()
    logging.info(f"Layer size: {_format_size(os.path.getsize(full_layer_file))}")
    return full_layer_file


def analyze_layer_file(layer_file: str, top_n: int):
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


def _log_dict(item_type: str, items: Dict, top_n: int) -> str:
    result = f"\n========== Top {top_n} {item_type} =========="
    for ext, size in sorted(items.items(), key=lambda x: x[1], reverse=True)[:top_n]:
        if size > 0:
            result += f"\n{ext}, {_format_size(size)}"
    logging.info(result)


def _format_size(size: int) -> str:
    for unit in ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB']:
        if size < 1024.0 or unit == 'PiB':
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"


def publish_layer(bucket: str, layer_file: str):
    import boto3
    layer_base_file_name = os.path.basename(layer_file)
    logging.info(f"Layer file name: {layer_base_file_name}, Layer size: {_format_size(os.path.getsize(layer_file))}")

    key = f"temp/{layer_base_file_name}"
    logging.info(f"Uploading to bucket: {bucket}. Key: {key}")
    s3 = boto3.client("s3")
    s3.upload_file(layer_file, bucket, key)

    client = boto3.client("lambda", region_name="us-east-1")
    response = client.publish_layer_version(
        LayerName="sklearn",
        Content={
            'S3Bucket': bucket,
            'S3Key': key
        },
    )
    s3.delete_object(Bucket=bucket, Key=key)
    if "Version" in response:
        logging.info(f"Layer version: {response['Version']}")
    else:
        logging.info(json.dumps(response, indent=4))


def run(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--layer", required=True, help="Layer name")
    parser.add_argument("-v", "--version", required=False, help="Layer version. If no version is given use default")
    parser.add_argument("-t", "--tag", required=False, default="latest", help="Lambda base image tag")
    parser.add_argument("-top", "--top", required=False, default=10,
                        help="Top item count in layer analysis. By default top 10 items are shown")
    parser.add_argument("-p", "--publish", required=False, default="false",
                        help="Publish lambda layer")
    parser.add_argument("-b", "--bucket", required=False,
                        help="S3 bucket to use, required for the publishing process")
    args = parser.parse_args(args=argv)

    layer_file = create_layer(args.layer, args.version, args.tag)
    # layer_file = get_output_folder() + "/" + get_layer_output_file(args.layer, args.version)
    analyze_layer_file(layer_file, args.top)
    if args.publish.lower() == "true":
        if args.bucket is None:
            logging.error("Bucket must be provided for publishing")
            exit(2)
        publish_layer(args.bucket, layer_file)


if __name__ == '__main__':
    fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
    run(sys.argv[1:])
