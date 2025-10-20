from __future__ import annotations

import base64
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

from config import boto3_client, boto3_resource, settings
from models.common import Image, Name, Product, ProductSummary, Profile, Report, ReportSummary
from utils.http import NotFound

# Simple in-memory store for offline/tests
_MEM_DB: Dict[str, Dict[str, Any]] = {
    "users": {},
    "products": {},
    "reports": {},
}


class UsersRepository:
    def __init__(self) -> None:
        self._use_mem = bool(os.getenv("K9_OFFLINE") or os.getenv("PYTEST_CURRENT_TEST"))
        if not self._use_mem:
            self._db = boto3_resource("dynamodb")
            self._table = self._db.Table(settings().users_table)

    def get(self, uid: str) -> Dict[str, Any]:
        if self._use_mem:
            item = _MEM_DB["users"].get(uid)
            if not item:
                raise NotFound("User not found")
            return item
        try:
            res = self._table.get_item(Key={"id": uid})
            if "Item" not in res:
                raise NotFound("User not found")
            return res["Item"]
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.get(uid)

    def list(self, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        if self._use_mem:
            items = list(_MEM_DB["users"].values())
            return items[:limit], None
        try:
            scan_kwargs: Dict[str, Any] = {"Limit": limit}
            if next_token:
                scan_kwargs["ExclusiveStartKey"] = {"id": next_token}
            res = self._table.scan(**scan_kwargs)
            items = res.get("Items", [])
            nt = res.get("LastEvaluatedKey", {}).get("id")
            return items, nt
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.list(limit, next_token)

    def put(self, item: Dict[str, Any]) -> None:
        if self._use_mem:
            _MEM_DB["users"][item["id"]] = item
            return
        try:
            self._table.put_item(Item=item)
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.put(item)

    def delete(self, uid: str) -> None:
        if self._use_mem:
            _MEM_DB["users"].pop(uid, None)
            return
        try:
            self._table.delete_item(Key={"id": uid})
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.delete(uid)

    def get_by_cognito_sub(self, sub: str) -> Dict[str, Any]:
        """Lookup a user profile by Cognito subject (sub) claim.

        In DynamoDB mode, expects a GSI on attribute 'cognitoSub' named 'cognitoSub-index'.
        In memory mode, scans the in-process map.
        """
        attr = "cognitoSub"
        if getattr(self, "_use_mem", False):
            for item in _MEM_DB["users"].values():
                if item.get(attr) == sub:
                    return item
            raise NotFound("User not found")
        try:
            res = self._table.query(
                IndexName="cognitoSub-index",
                KeyConditionExpression=Key(attr).eq(sub),
                Limit=1,
            )
            items = res.get("Items", [])
            if not items:
                raise NotFound("User not found")
            return items[0]
        except (NoCredentialsError, EndpointConnectionError):
            # fallback to mem if needed
            self._use_mem = True  # type: ignore[attr-defined]
            return self.get_by_cognito_sub(sub)

class ProductsRepository:
    def __init__(self) -> None:
        self._use_mem = bool(os.getenv("K9_OFFLINE") or os.getenv("PYTEST_CURRENT_TEST"))
        if not self._use_mem:
            self._db = boto3_resource("dynamodb")
            self._table = self._db.Table(settings().products_table)

    def get(self, pid: str) -> Dict[str, Any]:
        if self._use_mem:
            item = _MEM_DB["products"].get(pid)
            if not item:
                raise NotFound("Product not found")
            return item
        try:
            res = self._table.get_item(Key={"id": pid})
            if "Item" not in res:
                raise NotFound("Product not found")
            return res["Item"]
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.get(pid)

    def put(self, item: Dict[str, Any]) -> None:
        if self._use_mem:
            _MEM_DB["products"][item["id"]] = item
            return
        try:
            self._table.put_item(Item=item)
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.put(item)

    def delete(self, pid: str) -> None:
        if self._use_mem:
            _MEM_DB["products"].pop(pid, None)
            return
        try:
            self._table.delete_item(Key={"id": pid})
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.delete(pid)


class ReportsRepository:
    def __init__(self) -> None:
        self._use_mem = bool(os.getenv("K9_OFFLINE") or os.getenv("PYTEST_CURRENT_TEST"))
        if not self._use_mem:
            self._db = boto3_resource("dynamodb")
            self._table = self._db.Table(settings().reports_table)

    def get(self, rid: str) -> Dict[str, Any]:
        if self._use_mem:
            item = _MEM_DB["reports"].get(rid)
            if not item:
                raise NotFound("Report not found")
            return item
        try:
            res = self._table.get_item(Key={"id": rid})
            if "Item" not in res:
                raise NotFound("Report not found")
            return res["Item"]
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.get(rid)

    def list_by_author(self, author: str, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        if self._use_mem:
            items = [v for v in _MEM_DB["reports"].values() if v.get("author") == author]
            return items[:limit], None
        try:
            # For simplicity, assume a GSI on author
            kwargs: Dict[str, Any] = {
                "IndexName": "author-index",
                "KeyConditionExpression": Key("author").eq(author),
                "Limit": limit,
            }
            if next_token:
                kwargs["ExclusiveStartKey"] = {"id": next_token, "author": author}
            res = self._table.query(**kwargs)
            items = res.get("Items", [])
            nt = res.get("LastEvaluatedKey", {}).get("id")
            return items, nt
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.list_by_author(author, limit, next_token)

    def put(self, item: Dict[str, Any]) -> None:
        if self._use_mem:
            _MEM_DB["reports"][item["id"]] = item
            return
        try:
            self._table.put_item(Item=item)
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.put(item)

    def delete(self, rid: str) -> None:
        if self._use_mem:
            _MEM_DB["reports"].pop(rid, None)
            return
        try:
            self._table.delete_item(Key={"id": rid})
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.delete(rid)


class ImagesStorage:
    def __init__(self) -> None:
        self._use_mem = bool(os.getenv("K9_OFFLINE") or os.getenv("PYTEST_CURRENT_TEST"))
        if not self._use_mem:
            self._s3 = boto3_client("s3")
            self._bucket = settings().images_bucket

    def put_image(self, key: str, data: bytes, content_type: str = "image/png") -> None:
        if self._use_mem:
            # store in-process memory
            images: Dict[str, bytes] = _MEM_DB.setdefault("_images", {})  # type: ignore[assignment]
            images[key] = data
            return
        try:
            self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            self.put_image(key, data, content_type)

    def presign(self, key: str, expires: int = 3600) -> str:
        if self._use_mem:
            return f"https://local.test/{key}"
        try:
            return self._s3.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires,
            )
        except (NoCredentialsError, EndpointConnectionError):
            self._use_mem = True
            return self.presign(key, expires)
