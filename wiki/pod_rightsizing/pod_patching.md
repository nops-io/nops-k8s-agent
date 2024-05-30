# Pod Live-Patching

K8s later than 1.27 [introduced](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/) a new feature to `Resize CPU and Memory Resources assigned to Containers`.

However, this feature is in Alpha, so it's hidden under the feature gate by default ([InPlacePodVerticalScaling](https://kubernetes.io/blog/2023/05/12/in-place-pod-resize-alpha/)). And this feature gate cannot be enabled on the already running cluster - it needs to be re-created with an additional flag.

So, if agent verifies that the cluster version it runs in is `>=1.27` this feature gate is enabled - it will try to live-patch pod requests, otherwise it will re-create pods after the parent resource update.