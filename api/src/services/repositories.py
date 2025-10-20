from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from boto3.dynamodb.conditions import Key
from botocore.exceptions import EndpointConnectionError, NoCredentialsError

from config import boto3_client, boto3_resource, settings
from utils.http import NotFound


# Shared in-memory store for tests/local
_MEM_DB: Dict[str, Dict[str, Any]] = {
    "users": {},
    "products": {},
    "reports": {},
}


# Memory implementations
class MemoryUsersRepository:
    def get(self, uid: str) -> Dict[str, Any]:
        item = _MEM_DB["users"].get(uid)
        if not item:
            raise NotFound("User not found")
        return item

    def list(self, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        items = list(_MEM_DB["users"].values())
        return items[:limit], None

    def put(self, item: Dict[str, Any]) -> None:
        _MEM_DB["users"][item["id"]] = item

    def delete(self, uid: str) -> None:
        _MEM_DB["users"].pop(uid, None)

    def get_by_cognito_sub(self, sub: str) -> Dict[str, Any]:
        for item in _MEM_DB["users"].values():
            if item.get("cognitoSub") == sub:
                return item
        raise NotFound("User not found")


class MemoryProductsRepository:
    def get(self, pid: str) -> Dict[str, Any]:
        item = _MEM_DB["products"].get(pid)
        if not item:
            raise NotFound("Product not found")
        return item

    def put(self, item: Dict[str, Any]) -> None:
        _MEM_DB["products"][item["id"]] = item

    def delete(self, pid: str) -> None:
        _MEM_DB["products"].pop(pid, None)


class MemoryReportsRepository:
    def get(self, rid: str) -> Dict[str, Any]:
        item = _MEM_DB["reports"].get(rid)
        if not item:
            raise NotFound("Report not found")
        return item

    def list_by_author(self, author: str, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        items = [v for v in _MEM_DB["reports"].values() if v.get("author") == author]
        return items[:limit], None

    def put(self, item: Dict[str, Any]) -> None:
        _MEM_DB["reports"][item["id"]] = item

    def delete(self, rid: str) -> None:
        _MEM_DB["reports"].pop(rid, None)


class MemoryImagesStorage:
    def put_image(self, key: str, data: bytes, content_type: str = "image/png") -> None:
        images: Dict[str, bytes] = _MEM_DB.setdefault("_images", {})  # type: ignore[assignment]
        images[key] = data

    def presign(self, key: str, expires: int = 3600) -> str:
        return f"https://local.test/{key}"


# Cloud implementations (no auto-fallback)
class DynamoUsersRepository:
    def __init__(self) -> None:
        db = boto3_resource("dynamodb")
        self._table = db.Table(settings().users_table)

    def get(self, uid: str) -> Dict[str, Any]:
        res = self._table.get_item(Key={"id": uid})
        if "Item" not in res:
            raise NotFound("User not found")
        return res["Item"]

    def list(self, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        scan_kwargs: Dict[str, Any] = {"Limit": limit}
        if next_token:
            scan_kwargs["ExclusiveStartKey"] = {"id": next_token}
        res = self._table.scan(**scan_kwargs)
        items = res.get("Items", [])
        nt = res.get("LastEvaluatedKey", {}).get("id")
        return items, nt

    def put(self, item: Dict[str, Any]) -> None:
        self._table.put_item(Item=item)

    def delete(self, uid: str) -> None:
        self._table.delete_item(Key={"id": uid})

    def get_by_cognito_sub(self, sub: str) -> Dict[str, Any]:
        res = self._table.query(IndexName="cognitoSub-index", KeyConditionExpression=Key("cognitoSub").eq(sub), Limit=1)
        items = res.get("Items", [])
        if not items:
            raise NotFound("User not found")
        return items[0]


class DynamoProductsRepository:
    def __init__(self) -> None:
        db = boto3_resource("dynamodb")
        self._table = db.Table(settings().products_table)

    def get(self, pid: str) -> Dict[str, Any]:
        res = self._table.get_item(Key={"id": pid})
        if "Item" not in res:
            raise NotFound("Product not found")
        return res["Item"]

    def put(self, item: Dict[str, Any]) -> None:
        self._table.put_item(Item=item)

    def delete(self, pid: str) -> None:
        self._table.delete_item(Key={"id": pid})


class DynamoReportsRepository:
    def __init__(self) -> None:
        db = boto3_resource("dynamodb")
        self._table = db.Table(settings().reports_table)

    def get(self, rid: str) -> Dict[str, Any]:
        res = self._table.get_item(Key={"id": rid})
        if "Item" not in res:
            raise NotFound("Report not found")
        return res["Item"]

    def list_by_author(self, author: str, limit: int, next_token: Optional[str]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
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

    def put(self, item: Dict[str, Any]) -> None:
        self._table.put_item(Item=item)

    def delete(self, rid: str) -> None:
        self._table.delete_item(Key={"id": rid})


class S3ImagesStorage:
    def __init__(self) -> None:
        self._s3 = boto3_client("s3")
        self._bucket = settings().images_bucket

    def put_image(self, key: str, data: bytes, content_type: str = "image/png") -> None:
        self._s3.put_object(Bucket=self._bucket, Key=key, Body=data, ContentType=content_type)

    def presign(self, key: str, expires: int = 3600) -> str:
        return self._s3.generate_presigned_url(ClientMethod="get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=expires)


