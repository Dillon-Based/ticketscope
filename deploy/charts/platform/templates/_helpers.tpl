{{/* The labels every object this chart renders itself carries; call with the root context. */}}
{{- define "platform.labels" -}}
app.kubernetes.io/part-of: ticketscope
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
