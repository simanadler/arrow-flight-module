#
# Copyright 2020 IBM Corp.
# SPDX-License-Identifier: Apache-2.0
#
from urllib.parse import urlparse, quote
import requests
import json
from fybrik_python_logging import logger, DataSetID
from pyarrow.fs import S3FileSystem
from afm.filesystems.vault import get_credentials_from_vault

def s3filesystem_from_config(s3_config, datasetID):
    endpoint = s3_config.get('endpoint_url')
    region = s3_config.get('region')

    credentials = s3_config.get('credentials', {})
    access_key = credentials.get('accessKey')
    secret_key = credentials.get('secretKey')

    secret_provider = credentials.get('secretProvider')

    if 'vault_credentials' in s3_config:
        logger.trace("reading s3 configuration from vault",
                     extra={DataSetID: datasetID})
        access_key, secret_key = get_credentials_from_vault(
                s3_config.get('vault_credentials'), datasetID)
    elif secret_provider:
        logger.trace("reading s3 configuration from secret provider",
                     extra={DataSetID: datasetID})
        r = requests.get(secret_provider)
        r.raise_for_status()
        response = r.json()
        endpoint = response.get('endpoint_url') or endpoint
        region = response.get('region') or region
        access_key = response.get('access_key') or access_key
        secret_key = response.get('secret_key') or secret_key

    scheme, endpoint_override = _split_endpoint(endpoint)
    anonymous = not access_key

    return S3FileSystem(
        region=region,
        endpoint_override=endpoint_override,
        scheme=scheme,
        access_key=access_key,
        secret_key=secret_key,
        anonymous=anonymous
    )


def _split_endpoint(endpoint):
    if endpoint:
        parsed_endpoint = urlparse(endpoint)
        return parsed_endpoint.scheme, parsed_endpoint.netloc
    return None, None
