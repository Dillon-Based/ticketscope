{{/* Names: ticketscope-<component> (Consistency Conventions). */}}
{{- define "ticketscope.dbCluster" -}}ticketscope-db{{- end }}
{{- define "ticketscope.roSecret" -}}ticketscope-db-ro{{- end }}
{{- define "ticketscope.backupS3Secret" -}}ticketscope-backup-s3{{- end }}

{{- define "ticketscope.labels" -}}
app.kubernetes.io/part-of: ticketscope
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{- define "ticketscope.appImage" -}}
{{- $img := .Values.image.app -}}
{{- required "image.app.tag is required (the git SHA)" $img.tag | printf "%s:%s" $img.repository -}}
{{- end }}

{{- define "ticketscope.postgresImage" -}}
{{- $img := .Values.image.postgres -}}
{{- required "image.postgres.tag is required (the git SHA)" $img.tag | printf "%s:%s" $img.repository -}}
{{- end }}

{{/* Env for migrate and load: the app owner, from the CNPG-generated Secret (AD-7). */}}
{{- define "ticketscope.ownerDbEnv" -}}
- name: TICKETSCOPE_DB_HOST
  value: {{ include "ticketscope.dbCluster" . }}-rw
- name: TICKETSCOPE_DB_NAME
  value: app
- name: TICKETSCOPE_DB_USER
  valueFrom:
    secretKeyRef:
      name: {{ include "ticketscope.dbCluster" . }}-app
      key: username
- name: TICKETSCOPE_DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "ticketscope.dbCluster" . }}-app
      key: password
- name: TICKETSCOPE_DB_WAIT_TIMEOUT_SECONDS
  value: {{ .Values.jobs.dbWaitTimeoutSeconds | quote }}
{{- end }}

{{/* Embeddings are on when an asset is pinned, or (no pin) computeOnKind is set. A pinned
asset always wins over computeOnKind (story 4). Renders "true" or nothing. */}}
{{- define "ticketscope.embeddingsOn" -}}
{{- if or .Values.embeddings.assetVersion .Values.embeddings.computeOnKind -}}true{{- end -}}
{{- end }}

{{/* True (non-empty) only when load computes embeddings itself: no pinned asset. */}}
{{- define "ticketscope.embeddingsCompute" -}}
{{- if and .Values.embeddings.computeOnKind (not .Values.embeddings.assetVersion) -}}true{{- end -}}
{{- end }}

{{/* The embedding model id for api and load; rendered only when embeddings are on (AD-21). */}}
{{- define "ticketscope.embeddingEnv" -}}
{{- if include "ticketscope.embeddingsOn" . -}}
- name: TICKETSCOPE_EMBEDDING_MODEL_ID
  value: {{ required "embeddings.modelId is required" .Values.embeddings.modelId | quote }}
{{- end -}}
{{- end }}

{{/* OTLP export for every app process (AD-10). */}}
{{- define "ticketscope.otlpEnv" -}}
- name: TICKETSCOPE_OTLP_ENDPOINT
  value: {{ .Values.telemetry.otlpEndpoint | quote }}
{{- end }}

{{/* The hosts mcp answers to and its route matches: `hostname` plus `mcp.hosts`, as a JSON
list. A wildcard or an empty list fails the render (AD-5's DNS-rebinding guard). */}}
{{- define "ticketscope.mcpHosts" -}}
{{- $hosts := list -}}
{{- with .Values.hostname }}{{ $hosts = append $hosts . }}{{ end -}}
{{- range .Values.mcp.hosts }}{{ $hosts = append $hosts . }}{{ end -}}
{{- with .Values.mcp.tunnelHostname }}{{ $hosts = append $hosts . }}{{ end -}}
{{- $hosts = $hosts | uniq -}}
{{- if not $hosts -}}
{{- fail "hostname or mcp.hosts must name at least one host: mcp refuses an empty host list" -}}
{{- end -}}
{{- range $hosts -}}
{{- if or (not .) (contains "*" .) -}}
{{- fail (printf "mcp.hosts and hostname must not be empty or contain a wildcard: %q" .) -}}
{{- end -}}
{{- end -}}
{{- $hosts | toJson -}}
{{- end }}

{{/* The ClusterIP Service for a component's http port; call with (dict "root" . "component" "api"). */}}
{{- define "ticketscope.service" -}}
apiVersion: v1
kind: Service
metadata:
  name: ticketscope-{{ .component }}
  namespace: {{ .root.Release.Namespace }}
  labels:
    {{- include "ticketscope.labels" .root | nindent 4 }}
    app.kubernetes.io/component: {{ .component }}
spec:
  selector:
    app.kubernetes.io/instance: {{ .root.Release.Name }}
    app.kubernetes.io/component: {{ .component }}
  ports:
    - name: http
      port: 80
      targetPort: http
{{- end }}
