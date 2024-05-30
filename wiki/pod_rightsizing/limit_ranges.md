# Namespace Limit Ranges

In Kubernetes, a LimitRange is a policy to constrain resource allocations (to Pods or Containers) within a namespace. This feature allows administrators to specify the minimum and maximum compute resources a single pod or container may use, ensuring that the namespace does not allow the creation of pods or containers that are either too small or too large relative to the administrator’s settings. It also allows the setting of default request/limit values for pods or containers that do not specify their own requirements.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: example-limitrange
spec:
  limits:
  - type: Container
    min:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "1Gi"
```

Here's a breakdown of the key use cases for LimitRange:

- **Resource Allocation Constraints:** It helps ensure that Pods and Containers run with consistent resources in a namespace by setting default minimum and maximum values. This is useful in multi-tenant clusters, where you might want to ensure a fair allocation of resources among different teams or projects. 
- **Prevention of Resource Starvation:** By setting minimum resource requirements, you can prevent any single pod or container from using up an insignificant amount of resources, which could potentially leave it non-functional. 
- **Control Over Resource Overuse:** Similarly, by setting maximum limits, you can prevent any single pod or container from using excessive resources, which could impact other pods or the overall health of the cluster. 
- **Cost Management:** LimitRange can be used to control costs in a cloud environment by preventing pods from using resources beyond a certain limit, thus avoiding unexpected charges.


For the types of resources you can specify minimum and maximum requests in a LimitRange, they include:

- CPU 
- Memory 
- Storage 
- Ephemeral Storage

If we try to set Container requests/limits that do not satisfy one or multiple Namespace Limit Ranges - Pods won't start.

So, we need to check if the recommended value stays under the Limit Ranges:

- If Container-level Limit Range is set - validate all containers before patching, skip Containers that are out of Limit Range.
- TBD: If Pod-level Limit Range is set - validate the sum of container resources requests/limits before the patching so the total SUM of resources stays under the Limit Range for Pod.