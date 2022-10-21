""" Lambda function source code """

import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict

import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Attr

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])
DEFAULT_PAGINATION_SIZE = os.environ.get("DEFAULT_PAGINATION_SIZE", 5)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if len(logging.getLogger().handlers) > 0:
    # The Lambda environment pre-configures a handler logging to stderr. If a handler is already configured,
    # `.basicConfig` does not execute. Thus we set the level directly.
    logging.getLogger().setLevel(LOG_LEVEL)
else:
    logging.basicConfig(level=LOG_LEVEL)

logger = logging.getLogger()


def read_data(event):
    """Function for parsing GET requests

    Args:
        event (dict): event came from Api Gateway

    Returns:
        dict: Http response
    """
    query_params = event["queryStringParameters"]
    page = 1
    page_size = int(DEFAULT_PAGINATION_SIZE)
    if query_params:
        page = int(query_params.get("page", 1))
        page_size = int(query_params.get("page_size", DEFAULT_PAGINATION_SIZE))

    content = get_paginated_results(page - 1, page_size)

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "body": json.dumps(content, indent=4),
        "headers": {
            "content-type": "application/json",
        },
    }


def get_paginated_results(page, page_size):
    """Function implements pagination of the scanned items

    Args:
        page (int): Current page number, defaults to 1
        page_size (int): Maximum number of items in one page, defaults to 5

    Returns:
        list: List of items (dicts)
    """
    # Initialisation of variables
    lst = []
    curr_page = 0
    num = 0

    if page_size <= 0:
        return []

    for cnt, item in enumerate(get_scanned()):
        num += 1
        lst.append(item)

        if (
            num == page_size and curr_page == page
        ):  # To break a loop for returning value
            break

        if (
            num == page_size
        ):  # After each page counter 'num' equals to zero, lst accumulator cleaned and
            num = 0  # 'curr_page' variable increments
            lst = []
            curr_page += 1

    if curr_page != page:  # If requested page is greater than maximum page number
        lst = []

    return lst


def get_scanned():
    """Function that scans DynamoDB

    Yields:
        dict: item that is going to be yielded
    """
    response = table.scan()
    for item in response["Items"]:
        yield item
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        for item in response["Items"]:
            yield item


def put_item_safe(obj, *args, **kwargs):
    """Function handles an exception that may rise if duplicate entry will be detected

    Args:
        obj (object): DynamoDB table or batch object

    Returns:
        Any: False or Any
    """
    try:
        return obj.put_item(*args, **kwargs)
    except botocore.exceptions.ClientError as e:
        logger.warning(
            "Exception happened while calling %s" % "put_item_safe", exc_info=True
        )
        return False


def write_data(event):
    """Function for parsing POST requests

    Args:
        event (dict): event came from Api Gateway

    Returns:
        dict: Http response
    """
    body = event["body"]
    status_code = 201
    if isinstance(body, str):
        body = json.loads(body)

    if isinstance(body, dict):
        body["created"] = datetime.utcnow().isoformat()
        ret = put_item_safe(
            table, Item=body, ConditionExpression=Attr("title").not_exists()
        )
        if ret:
            details = {body["title"]: "Created"}
        else:
            details = {
                body["title"]: "Failed",
                "message": "Duplicate title detected.",
            }
            status_code = 400
    else:
        details = {
            "message": "Arrays are not supported.",
        }
        status_code = 400

    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "details": details,
            },
            indent=4,
        ),
    }


def default_handler(*args, **kwargs):
    """Default handler in case of the method is not implemented.

    Returns:
        dict: Http response
    """
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "error": "Method does not exist",
    }


HANDLER: defaultdict[Dict[str, Callable], Any] = defaultdict(
    default_handler,
    {
        "GET": read_data,
        "POST": write_data,
    },
)


def handler(event, context):
    """Lambda handler

    Args:
        event (dict): event came from Api Gateway
        context (dict): Runtime information about Lambda

    Returns:
        dict: Http response
    """
    logger.info("Event: %s", json.dumps(event))
    logger.info("Context: %s", context)
    return HANDLER[event["httpMethod"]](event)
