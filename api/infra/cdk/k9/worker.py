from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from aws_cdk import Duration
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_lambda_event_sources as sources
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as notifications
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from .config import (
    DynamoDBWorkerConfig,
    Environment,
    S3WorkerConfig,
    StageName,
    WorkerConfig,
)
from .function import create_function
from .manifest import DynamoDBEvent, S3Event, load_manifest
from .service import _construct_id

_S3_EVENTS = {
    "OBJECT_CREATED": s3.EventType.OBJECT_CREATED,
    "OBJECT_REMOVED": s3.EventType.OBJECT_REMOVED,
}


def dynamodb_filters(events: list[DynamoDBEvent]) -> list[Mapping[str, Any]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for event in events:
        image = "OldImage" if event.event == "REMOVE" else "NewImage"
        grouped[(event.event, image)].add(event.rule)
    return [
        lambda_.FilterCriteria.filter(
            {
                "eventName": lambda_.FilterRule.is_equal(event),
                "dynamodb": {image: {"type": {"S": sorted(rules)}}},
            }
        )
        for (event, image), rules in sorted(grouped.items())
    ]


def s3_filter(rule: str) -> s3.NotificationKeyFilter:
    if rule.count("*") > 1:
        raise ValueError(f"S3 notification rule has more than one wildcard: {rule!r}")
    prefix, _, suffix = rule.partition("*")
    return s3.NotificationKeyFilter(prefix=prefix or None, suffix=suffix or None)


class WorkerRegistration(Construct):
    def __init__(
        self,
        scope: Construct,
        name: str,
        config: WorkerConfig,
        *,
        stage: StageName,
        architecture: lambda_.Architecture,
        root: Path,
        environment: Environment,
        source_buckets: dict[str, s3.IBucket],
    ) -> None:
        super().__init__(scope, _construct_id("Worker", name))
        manifest = load_manifest(root, "workers", name)
        if manifest.routes:
            raise ValueError(f"Worker {name!r} must not declare HTTP routes")
        if not manifest.events:
            raise ValueError(f"Worker {name!r} has no event filters")
        if any(event.source != config.source for event in manifest.events):
            raise ValueError(f"Worker {name!r} contains events for the wrong source")

        self.function = create_function(
            self,
            root=root,
            kind="workers",
            name=name,
            stage=stage,
            architecture=architecture,
            config=config,
            environment=environment,
            manifest=manifest,
        )
        if isinstance(config, DynamoDBWorkerConfig):
            events = [
                event for event in manifest.events if isinstance(event, DynamoDBEvent)
            ]
            self._bind_dynamodb(config, events)
        elif isinstance(config, S3WorkerConfig):
            events = [event for event in manifest.events if isinstance(event, S3Event)]
            self._bind_s3(config, events, source_buckets)
        else:
            raise TypeError(f"Unsupported worker type: {type(config).__name__}")

        if parameter := config.opensearch_collection_arn_parameter:
            collection_arn = ssm.StringParameter.value_for_string_parameter(
                self, parameter
            )
            self.function.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["aoss:APIAccessAll"],
                    resources=[collection_arn],
                )
            )

    def _bind_dynamodb(
        self, config: DynamoDBWorkerConfig, events: list[DynamoDBEvent]
    ) -> None:
        table = dynamodb.Table.from_table_attributes(
            self,
            "SourceTable",
            table_name=config.table_name,
            table_stream_arn=ssm.StringParameter.value_for_string_parameter(
                self, config.stream_arn_parameter
            ),
        )
        table.grant_stream_read(self.function)
        self.function.add_event_source(
            sources.DynamoEventSource(
                table,
                starting_position=lambda_.StartingPosition.LATEST,
                batch_size=config.batch_size,
                retry_attempts=config.retry_attempts,
                report_batch_item_failures=config.report_batch_item_failures,
                bisect_batch_on_error=config.bisect_batch_on_error,
                filters=dynamodb_filters(events),
                max_record_age=(
                    Duration.seconds(config.max_record_age_seconds)
                    if config.max_record_age_seconds is not None
                    else None
                ),
                max_batching_window=(
                    Duration.seconds(config.max_batching_window_seconds)
                    if config.max_batching_window_seconds is not None
                    else None
                ),
                parallelization_factor=config.parallelization_factor,
            )
        )

    def _bind_s3(
        self,
        config: S3WorkerConfig,
        events: list[S3Event],
        source_buckets: dict[str, s3.IBucket],
    ) -> None:
        bucket = source_buckets.get(config.bucket_name)
        if bucket is None:
            bucket = s3.Bucket.from_bucket_name(
                self, "SourceBucket", config.bucket_name
            )
            source_buckets[config.bucket_name] = bucket
        destination = notifications.LambdaDestination(self.function)
        for event in events:
            bucket.add_event_notification(
                _S3_EVENTS[event.event],
                destination,
                s3_filter(event.rule),
            )
