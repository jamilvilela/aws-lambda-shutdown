"""Tests for service handlers."""

from unittest.mock import MagicMock

import pytest

from src.services.ec2_handler import EC2Handler
from src.services.rds_handler import RDSHandler
from src.services.ecs_handler import ECSHandler
from src.services.glue_handler import GlueHandler
from src.services.aurora_handler import AuroraHandler
from src.services.batch_handler import BatchHandler
from src.services.dms_handler import DMSHandler
from src.services.dms_serverless_handler import DMSServerlessHandler


def test_ec2_handler_stops_all_active():
    ec2 = MagicMock()
    ec2.get_paginator.return_value.paginate.return_value = [
        {"Reservations": [{"Instances": [{"InstanceId": "i-1"}, {"InstanceId": "i-2"}]}]}
    ]
    handler = EC2Handler(ec2)
    failures = handler.run()
    assert failures == []
    ec2.stop_instances.assert_any_call(InstanceIds=["i-1"], Force=True)
    ec2.stop_instances.assert_any_call(InstanceIds=["i-2"], Force=True)
    assert ec2.stop_instances.call_count == 2


def test_ec2_handler_no_instances():
    ec2 = MagicMock()
    ec2.get_paginator.return_value.paginate.return_value = [{"Reservations": []}]
    handler = EC2Handler(ec2)
    failures = handler.run()
    assert failures == []
    ec2.stop_instances.assert_not_called()


def test_rds_handler_stops_active():
    rds = MagicMock()
    rds.get_paginator.return_value.paginate.return_value = [
        {"DBInstances": [
            {"DBInstanceIdentifier": "db-1", "DBInstanceStatus": "available"},
            {"DBInstanceIdentifier": "db-2", "DBInstanceStatus": "stopped"},
        ]}
    ]
    handler = RDSHandler(rds)
    failures = handler.run()
    assert failures == []
    rds.stop_db_instance.assert_called_once_with(DBInstanceIdentifier="db-1")


def test_ecs_handler_scales_to_zero():
    ecs = MagicMock()
    ecs.get_paginator.return_value.paginate.side_effect = [
        [{"clusterArns": ["arn:aws:ecs:us-east-1:123:cluster/my-cluster"]}],
        [{"serviceArns": ["arn:aws:ecs:us-east-1:123:service/my-service"]}],
    ]
    ecs.describe_services.return_value = {
        "services": [{"serviceName": "my-service", "runningCount": 2}]
    }
    handler = ECSHandler(ecs)
    failures = handler.run()
    assert failures == []
    ecs.update_service.assert_called_once_with(
        cluster="arn:aws:ecs:us-east-1:123:cluster/my-cluster",
        service="my-service",
        desiredCount=0,
    )


def test_ecs_handler_skips_zero_running():
    ecs = MagicMock()
    ecs.get_paginator.return_value.paginate.side_effect = [
        [{"clusterArns": ["arn:aws:ecs:us-east-1:123:cluster/my-cluster"]}],
        [{"serviceArns": ["arn:aws:ecs:us-east-1:123:service/my-service"]}],
    ]
    ecs.describe_services.return_value = {
        "services": [{"serviceName": "my-service", "runningCount": 0}]
    }
    handler = ECSHandler(ecs)
    failures = handler.run()
    assert failures == []
    ecs.update_service.assert_not_called()


def test_glue_handler_batch_stops_running():
    glue = MagicMock()
    glue.get_paginator.return_value.paginate.side_effect = [
        [{"Jobs": [
            {"Name": "job-batch", "Command": {"Name": "glueetl"}},
            {"Name": "job-stream", "Command": {"Name": "gluestreaming"}},
        ]}],
        [{"JobRuns": [
            {"Id": "run-1", "JobRunState": "RUNNING"},
            {"Id": "run-2", "JobRunState": "SUCCEEDED"},
        ]}],
    ]
    handler = GlueHandler(glue, service_name="glue-batch")
    failures = handler.run()
    assert failures == []
    glue.batch_stop_job_run.assert_called_once_with(JobName="job-batch", JobRunIds=["run-1"])


def test_glue_handler_stream_stops_running():
    glue = MagicMock()
    glue.get_paginator.return_value.paginate.side_effect = [
        [{"Jobs": [
            {"Name": "job-batch", "Command": {"Name": "glueetl"}},
            {"Name": "job-stream", "Command": {"Name": "gluestreaming"}},
        ]}],
        [{"JobRuns": [
            {"Id": "run-1", "JobRunState": "RUNNING"},
        ]}],
    ]
    handler = GlueHandler(glue, service_name="glue-stream")
    failures = handler.run()
    assert failures == []
    glue.batch_stop_job_run.assert_called_once_with(JobName="job-stream", JobRunIds=["run-1"])


def test_aurora_handler_stops_active():
    rds = MagicMock()
    rds.get_paginator.return_value.paginate.return_value = [
        {"DBClusters": [
            {"DBClusterIdentifier": "aurora-1", "Status": "available"},
            {"DBClusterIdentifier": "aurora-2", "Status": "stopped"},
        ]}
    ]
    handler = AuroraHandler(rds)
    failures = handler.run()
    assert failures == []
    rds.stop_db_cluster.assert_called_once_with(DBClusterIdentifier="aurora-1")


def test_batch_handler_terminates_running():
    batch = MagicMock()
    batch.get_paginator.return_value.paginate.side_effect = [
        [{"jobSummaryList": [{"jobId": "job-1"}]}],  # RUNNING
        [{"jobSummaryList": []}],  # SUBMITTED
        [{"jobSummaryList": []}],  # PENDING
        [{"jobSummaryList": []}],  # RUNNABLE
        [{"jobSummaryList": []}],  # STARTING
    ]
    handler = BatchHandler(batch)
    failures = handler.run()
    assert failures == []
    batch.terminate_job.assert_called_once_with(
        jobId="job-1", reason="Forced shutdown by aws-lambda-shutdown"
    )


def test_dms_handler_stops_tasks_and_instances():
    dms = MagicMock()
    dms.get_paginator.return_value.paginate.side_effect = [
        [{"ReplicationTasks": [
            {"ReplicationTaskArn": "arn:task-1", "Status": "running"},
            {"ReplicationTaskArn": "arn:task-2", "Status": "stopped"},
        ]}],
        [{"ReplicationInstances": [
            {"ReplicationInstanceArn": "arn:inst-1", "ReplicationInstanceStatus": "running"},
            {"ReplicationInstanceArn": "arn:inst-2", "ReplicationInstanceStatus": "creating"},
        ]}],
    ]
    handler = DMSHandler(dms)
    failures = handler.run()
    assert failures == []
    dms.stop_replication_task.assert_called_once_with(ReplicationTaskArn="arn:task-1")
    dms.stop_replication_instance.assert_called_once_with(ReplicationInstanceArn="arn:inst-1")


def test_dms_serverless_handler_stops_configs():
    dms = MagicMock()
    dms.get_paginator.return_value.paginate.return_value = [
        {"ReplicationConfigs": [
            {"ReplicationConfigArn": "arn:config-1", "Status": "running"},
            {"ReplicationConfigArn": "arn:config-2", "Status": "stopped"},
        ]}
    ]
    handler = DMSServerlessHandler(dms)
    failures = handler.run()
    assert failures == []
    dms.stop_replication.assert_called_once_with(ReplicationConfigArn="arn:config-1")