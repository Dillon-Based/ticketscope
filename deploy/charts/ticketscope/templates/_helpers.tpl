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

{{/* The embedding model id for api and load; rendered only when embeddings are on (AD-21). */}}
{{- define "ticketscope.embeddingEnv" -}}
{{- if .Values.embeddings.computeOnKind -}}
- name: TICKETSCOPE_EMBEDDING_MODEL_ID
  value: {{ required "embeddings.modelId is required" .Values.embeddings.modelId | quote }}
{{- end -}}
{{- end }}

{{/* OTLP export for every app process (AD-10). */}}
{{- define "ticketscope.otlpEnv" -}}
- name: TICKETSCOPE_OTLP_ENDPOINT
  value: {{ .Values.telemetry.otlpEndpoint | quote }}
{{- end }}
