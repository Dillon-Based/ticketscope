# Failure drill (story 5.8, R10)

Result: not yet run

`scripts/failure-drill.sh` terminates the node holding the primary of a live two-instance
environment while a probe searches through the public hostname every second. A person runs it,
last in the live window, and the rendered, masked record replaces this skeleton.

```text
scripts/failure-drill.sh --kubeconfig <admin kubeconfig> --url https://<hostname> --out <dir>
```
