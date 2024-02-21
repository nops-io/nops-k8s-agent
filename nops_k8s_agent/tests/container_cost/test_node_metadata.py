from nops_k8s_agent.container_cost.node_metadata import NodeMetadata


def test_custom_metrics_function_with_varied_data():
    node_metadata = NodeMetadata(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")

    varied_data_cases = [
        {
            "metric": {
                "provider_id": "aws://us-west-2/1bb72fc007-d59a588733124b01b54ed242db0b51ad/fargate-ip-10-50-44-142.us-west-2.compute.internal"
            },
            "expected": "fargate-ip-10-50-44-142.us-west-2.compute.internal",
        },
        {"metric": {"provider_id": "aws:///us-west-2/i-024a9b9e9e148ce8d"}, "expected": "i-024a9b9e9e148ce8d"},
        {
            "metric": {
                "provider_id": "fargate:///us-west-2/1bb72fc007-d59a588733124b01b54ed242db0b51ad/fargate-ip-10-50-45-143.us-west-2.compute.internal"
            },
            "expected": "fargate-ip-10-50-45-143.us-west-2.compute.internal",
        },
    ]

    for case in varied_data_cases:
        instance_id = node_metadata.custom_metrics_function(case)
        assert (
            instance_id == case["expected"]
        ), f"custom_metrics_function failed for {case['metric']['provider_id']} - expected {case['expected']}, got {instance_id}"
