{{- define "nops-k8s-agent.name" -}}
{{- default .Chart.Name .Values.nopsAgent.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "nops-k8s-agent.fullname" -}}
{{- if .Values.nopsAgent.fullnameOverride }}
{{- .Values.nopsAgent.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nopsAgent.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- define "nops-k8s-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "nops-k8s-agent.labels" -}}
helm.sh/chart: {{ include "nops-k8s-agent.chart" . }}
{{ include "nops-k8s-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "nops-k8s-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "nops-k8s-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "nops-k8s-agent.serviceAccountName" -}}
{{- if .Values.nopsAgent.serviceAccount.create }}
{{- default (include "nops-k8s-agent.fullname" .) .Values.nopsAgent.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.nopsAgent.serviceAccount.name }}
{{- end }}
{{- end }}

##### PROMETHEUS SERVER #####

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "prometheus.name" -}}
{{- default .Chart.Name .Values.prometheus.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "prometheus.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create labels for prometheus
*/}}
{{- define "prometheus.common.matchLabels" -}}
app.kubernetes.io/name: {{ include "prometheus.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create unified labels for prometheus components
*/}}
{{- define "prometheus.common.metaLabels" -}}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
helm.sh/chart: {{ include "prometheus.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ include "prometheus.name" . }}
{{- with .Values.prometheus.commonMetaLabels}}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "prometheus.server.labels" -}}
{{ include "prometheus.server.matchLabels" . }}
{{ include "prometheus.common.metaLabels" . }}
{{- end -}}

{{- define "prometheus.server.matchLabels" -}}
app.kubernetes.io/component: {{ .Values.prometheus.server.name }}
{{ include "prometheus.common.matchLabels" . }}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "prometheus.fullname" -}}
{{- if .Values.prometheus.fullnameOverride -}}
{{- .Values.prometheus.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.prometheus.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create a fully qualified ClusterRole name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "prometheus.clusterRoleName" -}}
{{- if .Values.prometheus.server.clusterRoleNameOverride -}}
{{ .Values.prometheus.server.clusterRoleNameOverride | trunc 63 | trimSuffix "-" }}
{{- else -}}
{{ include "prometheus.server.fullname" . }}
{{- end -}}
{{- end -}}

{{/*
Create a fully qualified alertmanager name for communicating with the user via NOTES.txt
*/}}
{{- define "prometheus.alertmanager.fullname" -}}
{{- template "alertmanager.fullname" .Subcharts.alertmanager -}}
{{- end -}}

{{/*
Create a fully qualified Prometheus server name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "prometheus.server.fullname" -}}
{{- if .Values.prometheus.server.fullnameOverride -}}
{{- .Values.prometheus.server.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.prometheus.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- printf "%s-%s" .Release.Name .Values.prometheus.server.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s-%s" .Release.Name $name .Values.prometheus.server.name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Get KubeVersion removing pre-release information.
*/}}
{{- define "prometheus.kubeVersion" -}}
  {{- default .Capabilities.KubeVersion.Version (regexFind "v[0-9]+\\.[0-9]+\\.[0-9]+" .Capabilities.KubeVersion.Version) -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for deployment.
*/}}
{{- define "prometheus.deployment.apiVersion" -}}
{{- print "apps/v1" -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for networkpolicy.
*/}}
{{- define "prometheus.networkPolicy.apiVersion" -}}
{{- print "networking.k8s.io/v1" -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for poddisruptionbudget.
*/}}
{{- define "prometheus.podDisruptionBudget.apiVersion" -}}
{{- if .Capabilities.APIVersions.Has "policy/v1" }}
{{- print "policy/v1" -}}
{{- else -}}
{{- print "policy/v1beta1" -}}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for rbac.
*/}}
{{- define "rbac.apiVersion" -}}
{{- if .Capabilities.APIVersions.Has "rbac.authorization.k8s.io/v1" }}
{{- print "rbac.authorization.k8s.io/v1" -}}
{{- else -}}
{{- print "rbac.authorization.k8s.io/v1beta1" -}}
{{- end -}}
{{- end -}}

{{/*
Return the appropriate apiVersion for ingress.
*/}}
{{- define "ingress.apiVersion" -}}
  {{- if and (.Capabilities.APIVersions.Has "networking.k8s.io/v1") (semverCompare ">= 1.19.x" (include "prometheus.kubeVersion" .)) -}}
      {{- print "networking.k8s.io/v1" -}}
  {{- else if .Capabilities.APIVersions.Has "networking.k8s.io/v1beta1" -}}
    {{- print "networking.k8s.io/v1beta1" -}}
  {{- else -}}
    {{- print "extensions/v1beta1" -}}
  {{- end -}}
{{- end -}}

{{/*
Return if ingress is stable.
*/}}
{{- define "ingress.isStable" -}}
  {{- eq (include "ingress.apiVersion" .) "networking.k8s.io/v1" -}}
{{- end -}}

{{/*
Return if ingress supports ingressClassName.
*/}}
{{- define "ingress.supportsIngressClassName" -}}
  {{- or (eq (include "ingress.isStable" .) "true") (and (eq (include "ingress.apiVersion" .) "networking.k8s.io/v1beta1") (semverCompare ">= 1.18.x" (include "prometheus.kubeVersion" .))) -}}
{{- end -}}

{{/*
Return if ingress supports pathType.
*/}}
{{- define "ingress.supportsPathType" -}}
  {{- or (eq (include "ingress.isStable" .) "true") (and (eq (include "ingress.apiVersion" .) "networking.k8s.io/v1beta1") (semverCompare ">= 1.18.x" (include "prometheus.kubeVersion" .))) -}}
{{- end -}}

{{/*
Create the name of the service account to use for the server component
*/}}
{{- define "prometheus.serviceAccountName.server" -}}
{{- if .Values.prometheus.serviceAccounts.server.create -}}
    {{ default (include "prometheus.server.fullname" .) .Values.prometheus.serviceAccounts.server.name }}
{{- else -}}
    {{ default "default" .Values.prometheus.serviceAccounts.server.name }}
{{- end -}}
{{- end -}}

{{/*
Define the prometheus.namespace template if set with forceNamespace or .Release.Namespace is set
*/}}
{{- define "prometheus.namespace" -}}
  {{- default .Release.Namespace .Values.prometheus.forceNamespace -}}
{{- end }}

{{/*
Define template prometheus.namespaces producing a list of namespaces to monitor
*/}}
{{- define "prometheus.namespaces" -}}
{{- $namespaces := list }}
{{- if and .Values.prometheus.rbac.create .Values.prometheus.server.useExistingClusterRoleName }}
  {{- if .Values.prometheus.server.namespaces -}}
    {{- range $ns := join "," .Values.prometheus.server.namespaces | split "," }}
      {{- $namespaces = append $namespaces (tpl $ns $) }}
    {{- end -}}
  {{- end -}}
  {{- if .Values.prometheus.server.releaseNamespace -}}
    {{- $namespaces = append $namespaces (include "prometheus.namespace" .) }}
  {{- end -}}
{{- end -}}
{{ mustToJson $namespaces }}
{{- end -}}

{{/*
Define prometheus.server.remoteWrite producing a list of remoteWrite configurations with URL templating
*/}}
{{- define "prometheus.server.remoteWrite" -}}
{{- $remoteWrites := list }}
{{- range $remoteWrite := .Values.prometheus.server.remoteWrite }}
  {{- $remoteWrites = tpl $remoteWrite.url $ | set $remoteWrite "url" | append $remoteWrites }}
{{- end -}}
{{ toYaml $remoteWrites }}
{{- end -}}

{{/*
Define prometheus.server.remoteRead producing a list of remoteRead configurations with URL templating
*/}}
{{- define "prometheus.server.remoteRead" -}}
{{- $remoteReads := list }}
{{- range $remoteRead := .Values.prometheus.server.remoteRead }}
  {{- $remoteReads = tpl $remoteRead.url $ | set $remoteRead "url" | append $remoteReads }}
{{- end -}}
{{ toYaml $remoteReads }}
{{- end -}}

##### PROMETHEUS NODE EXPORTER #####

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "prometheus-node-exporter.name" -}}
{{- default .Chart.Name .Values.prometheus.nodeExporter.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "prometheus-node-exporter.fullname" -}}
{{- if .Values.prometheus.nodeExporter.fullnameOverride }}
{{- .Values.prometheus.nodeExporter.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.prometheus.nodeExporter.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "prometheus-node-exporter.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "prometheus-node-exporter.labels" -}}
helm.sh/chart: {{ include "prometheus-node-exporter.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: metrics
app.kubernetes.io/part-of: {{ include "prometheus-node-exporter.name" . }}
{{ include "prometheus-node-exporter.selectorLabels" . }}
{{- with .Chart.AppVersion }}
app.kubernetes.io/version: {{ . | quote }}
{{- end }}
{{- with .Values.prometheus.nodeExporter.podLabels }}
{{ toYaml . }}
{{- end }}
{{- if .Values.prometheus.nodeExporter.releaseLabel }}
release: {{ .Release.Name }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "prometheus-node-exporter.selectorLabels" -}}
app.kubernetes.io/name: {{ include "prometheus-node-exporter.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}


{{/*
Create the name of the service account to use
*/}}
{{- define "prometheus-node-exporter.serviceAccountName" -}}
{{- if .Values.prometheus.nodeExporter.serviceAccount.create }}
{{- default (include "prometheus-node-exporter.fullname" .) .Values.prometheus.nodeExporter.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.prometheus.nodeExporter.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Allow the release namespace to be overridden for multi-namespace deployments in combined charts
*/}}
{{- define "prometheus-node-exporter.namespace" -}}
{{- if .Values.prometheus.nodeExporter.namespaceOverride }}
{{- .Values.prometheus.nodeExporter.namespaceOverride }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Create the namespace name of the service monitor
*/}}
{{- define "prometheus-node-exporter.monitor-namespace" -}}
{{- if .Values.prometheus.nodeExporter.namespaceOverride }}
{{- .Values.prometheus.nodeExporter.namespaceOverride }}
{{- else }}
{{- if .Values.prometheus.nodeExporter.prometheus.monitor.namespace }}
{{- .Values.prometheus.nodeExporter.prometheus.monitor.namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}
{{- end }}

{{/* Sets default scrape limits for servicemonitor */}}
{{- define "servicemonitor.scrapeLimits" -}}
{{- with .sampleLimit }}
sampleLimit: {{ . }}
{{- end }}
{{- with .targetLimit }}
targetLimit: {{ . }}
{{- end }}
{{- with .labelLimit }}
labelLimit: {{ . }}
{{- end }}
{{- with .labelNameLengthLimit }}
labelNameLengthLimit: {{ . }}
{{- end }}
{{- with .labelValueLengthLimit }}
labelValueLengthLimit: {{ . }}
{{- end }}
{{- end }}

{{/*
Formats imagePullSecrets. Input is (dict "Values" .Values "imagePullSecrets" .{specific imagePullSecrets})
*/}}
{{- define "prometheus-node-exporter.imagePullSecrets" -}}
{{- range (concat .Values.global.imagePullSecrets .imagePullSecrets) }}
  {{- if eq (typeOf .) "map[string]interface {}" }}
- {{ toYaml . | trim }}
  {{- else }}
- name: {{ . }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
Create the namespace name of the pod monitor
*/}}
{{- define "prometheus-node-exporter.podmonitor-namespace" -}}
{{- if .Values.prometheus.nodeExporter.namespaceOverride }}
{{- .Values.prometheus.nodeExporter.namespaceOverride }}
{{- else }}
{{- if .Values.prometheus.nodeExporter.prometheus.podMonitor.namespace }}
{{- .Values.prometheus.nodeExporter.prometheus.podMonitor.namespace }}
{{- else }}
{{- .Release.Namespace }}
{{- end }}
{{- end }}
{{- end }}

{{/* Sets default scrape limits for podmonitor */}}
{{- define "podmonitor.scrapeLimits" -}}
{{- with .sampleLimit }}
sampleLimit: {{ . }}
{{- end }}
{{- with .targetLimit }}
targetLimit: {{ . }}
{{- end }}
{{- with .labelLimit }}
labelLimit: {{ . }}
{{- end }}
{{- with .labelNameLengthLimit }}
labelNameLengthLimit: {{ . }}
{{- end }}
{{- with .labelValueLengthLimit }}
labelValueLengthLimit: {{ . }}
{{- end }}
{{- end }}

{{/* Sets sidecar volumeMounts */}}
{{- define "prometheus-node-exporter.sidecarVolumeMounts" -}}
{{- range $_, $mount := $.Values.prometheus.nodeExporter.sidecarVolumeMount }}
- name: {{ $mount.name }}
  mountPath: {{ $mount.mountPath }}
  readOnly: {{ $mount.readOnly }}
{{- end }}
{{- range $_, $mount := $.Values.prometheus.nodeExporter.sidecarHostVolumeMounts }}
- name: {{ $mount.name }}
  mountPath: {{ $mount.mountPath }}
  readOnly: {{ $mount.readOnly }}
{{- if $mount.mountPropagation }}
  mountPropagation: {{ $mount.mountPropagation }}
{{- end }}
{{- end }}
{{- end }}

##### OPENCOST #####

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "opencost.name" -}}
  {{- default .Chart.Name .Values.opencost.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opencost.chart" -}}
  {{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opencost.fullname" -}}
  {{- if .Values.opencost.fullnameOverride -}}
    {{- .Values.opencost.fullnameOverride | trunc 63 | trimSuffix "-" -}}
  {{- else -}}
    {{- $name := default .Chart.Name .Values.opencost.nameOverride -}}
    {{- if contains $name .Release.Name -}}
      {{- .Release.Name | trunc 63 | trimSuffix "-" -}}
    {{- else -}}
      {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/*
Allow the release namespace to be overridden
*/}}
{{- define "opencost.namespace" -}}
  {{- if .Values.opencost.namespaceOverride -}}
    {{- .Values.opencost.namespaceOverride -}}
  {{- else -}}
    {{- .Release.Namespace -}}
  {{- end -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
*/}}
{{- define "opencost.prometheus.secretname" -}}
  {{- if .Values.opencost.opencost.prometheus.secret_name -}}
    {{- .Values.opencost.opencost.prometheus.secret_name -}}
  {{- else -}}
    {{- include "opencost.fullname" . -}}
  {{- end -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "opencost.labels" -}}
helm.sh/chart: {{ include "opencost.chart" . }}
{{ include "opencost.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/part-of: {{ template "opencost.name" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Values.opencost.commonLabels}}
{{ toYaml .Values.opencost.commonLabels }}
{{- end }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "opencost.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opencost.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the controller service account to use
*/}}
{{- define "opencost.serviceAccountName" -}}
  {{- if .Values.opencost.serviceAccount.create -}}
    {{- default (include "opencost.fullname" .) .Values.opencost.serviceAccount.name }}
  {{- else -}}
    {{- default "default" .Values.opencost.serviceAccount.name }}
  {{- end -}}
{{- end -}}

{{/*
Create the name of the controller service account to use
*/}}
{{- define "opencost.prometheusServerEndpoint" -}}
  {{- if .Values.opencost.opencost.prometheus.external.enabled -}}
    {{ tpl .Values.opencost.opencost.prometheus.external.url . }}
  {{- else if (and .Values.opencost.opencost.prometheus.amp.enabled .Values.opencost.opencost.sigV4Proxy) -}}
    {{- $port := .Values.opencost.opencost.sigV4Proxy.port | int }}
    {{- $ws := .Values.opencost.opencost.prometheus.amp.workspaceId }}
    {{- printf "http://localhost:%d/workspaces/%v" $port $ws -}}
  {{- else -}}
    {{- $host := tpl .Values.opencost.opencost.prometheus.internal.serviceName . }}
    {{- $ns := tpl .Values.opencost.opencost.prometheus.internal.namespaceName . }}
    {{- $port := .Values.opencost.opencost.prometheus.internal.port | int }}
    {{- printf "http://%s.%s.svc.cluster.local:%d" $host $ns $port -}}
  {{- end -}}
{{- end -}}

{{/*
Check that either thanos external or internal is defined
*/}}
{{- define "opencost.thanosServerEndpoint" -}}
  {{- if .Values.opencost.opencost.prometheus.thanos.external.enabled -}}
    {{ .Values.opencost.opencost.prometheus.thanos.external.url }}
  {{- else -}}
    {{- $host := .Values.opencost.opencost.prometheus.thanos.internal.serviceName }}
    {{- $ns := .Values.opencost.opencost.prometheus.thanos.internal.namespaceName }}
    {{- $port := .Values.opencost.opencost.prometheus.thanos.internal.port | int }}
    {{- printf "http://%s.%s.svc.cluster.local:%d" $host $ns $port -}}
  {{- end -}}
{{- end -}}

{{/*
Check that the config is valid
*/}}
{{- define "isPrometheusConfigValid" -}}
  {{- $prometheusModes := add .Values.opencost.opencost.prometheus.external.enabled .Values.opencost.opencost.prometheus.internal.enabled .Values.opencost.opencost.prometheus.amp.enabled | int }}
  {{- if gt $prometheusModes 1 -}}
    {{- fail "Only use one of the prometheus setups: internal, external, or amp" -}}
  {{- end -}}
  {{- if .Values.opencost.opencost.prometheus.thanos.enabled -}}
    {{- if and .Values.opencost.opencost.prometheus.thanos.external.enabled .Values.opencost.opencost.prometheus.thanos.internal.enabled -}}
      {{- fail "Only use one of the thanos setups: internal or external" -}}
    {{- end -}}
  {{- end -}}
{{- end -}}

{{/*
Define opencost config file name
*/}}
{{- define "opencost.configFileName" -}}
  {{- if  eq .Values.opencost.opencost.customPricing.provider "custom" -}}
    {{- print "default" -}}
  {{- else -}}
    {{- .Values.opencost.opencost.customPricing.provider -}}
  {{- end -}}
{{- end -}}

{{/*
Get api version of networking.k8s.io
*/}}
{{- define "networkingAPIVersion" -}}
{{- if .Capabilities.APIVersions.Has "networking.k8s.io/v1" }}
apiVersion: networking.k8s.io/v1
{{- else if .Capabilities.APIVersions.Has "networking.k8s.io/v1beta1" }}
apiVersion: networking.k8s.io/v1beta1
{{- end }}
{{- end -}}

{{- define "opencost.imageTag" -}}
{{ .Values.opencost.opencost.exporter.image.tag | default (printf "%s" .Chart.AppVersion) }}
{{- end -}}

{{- define "opencost.fullImageName" -}}
{{- if .Values.opencost.opencost.exporter.image.fullImageName }}
{{- .Values.opencost.opencost.exporter.image.fullImageName -}}
{{- else}}
{{- .Values.opencost.opencost.exporter.image.registry -}}/{{- .Values.opencost.opencost.exporter.image.repository -}}:{{- include "opencost.imageTag" . -}}
{{- end -}}
{{- end -}}

{{- define "opencostUi.imageTag" -}}
{{- .Values.opencost.opencost.ui.image.tag | default (printf "%s" .Chart.AppVersion) -}}
{{- end -}}

{{- define "opencostUi.fullImageName" -}}
{{- if .Values.opencost.opencost.ui.image.fullImageName }}
{{- .Values.opencost.opencost.ui.image.fullImageName -}}
{{- else}}
{{- .Values.opencost.opencost.ui.image.registry -}}/{{- .Values.opencost.opencost.ui.image.repository -}}:{{- include "opencostUi.imageTag" . -}}
{{- end -}}
{{- end -}}

##### KUBE STATE METRICS #####

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "kube-state-metrics.name" -}}
{{- default .Chart.Name .Values.prometheus.kubeStateMetrics.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "kube-state-metrics.fullname" -}}
{{- if .Values.prometheus.kubeStateMetrics.fullnameOverride -}}
{{- .Values.prometheus.kubeStateMetrics.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.prometheus.kubeStateMetrics.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "kube-state-metrics.serviceAccountName" -}}
{{- if .Values.prometheus.kubeStateMetrics.serviceAccount.create -}}
    {{ default (include "kube-state-metrics.fullname" .) .Values.prometheus.kubeStateMetrics.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.prometheus.kubeStateMetrics.serviceAccount.name }}
{{- end -}}
{{- end -}}

{{/*
Allow the release namespace to be overridden for multi-namespace deployments in combined charts
*/}}
{{- define "kube-state-metrics.namespace" -}}
  {{- if .Values.prometheus.kubeStateMetrics.namespaceOverride -}}
    {{- .Values.prometheus.kubeStateMetrics.namespaceOverride -}}
  {{- else -}}
    {{- .Release.Namespace -}}
  {{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "kube-state-metrics.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Generate basic labels
*/}}
{{- define "kube-state-metrics.labels" }}
helm.sh/chart: {{ template "kube-state-metrics.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/component: metrics
app.kubernetes.io/part-of: {{ template "kube-state-metrics.name" . }}
{{- include "kube-state-metrics.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
{{- if .Values.prometheus.kubeStateMetrics.customLabels }}
{{ toYaml .Values.prometheus.kubeStateMetrics.customLabels }}
{{- end }}
{{- if .Values.prometheus.kubeStateMetrics.releaseLabel }}
release: {{ .Release.Name }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "kube-state-metrics.selectorLabels" }}
{{- if .Values.prometheus.kubeStateMetrics.selectorOverride }}
{{ toYaml .Values.prometheus.kubeStateMetrics.selectorOverride }}
{{- else }}
app.kubernetes.io/name: {{ include "kube-state-metrics.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
{{- end }}

{{/*
Formats imagePullSecrets. Input is (dict "Values" .Values "imagePullSecrets" .{specific imagePullSecrets})
*/}}
{{- define "kube-state-metrics.imagePullSecrets" -}}
{{- range (concat .Values.prometheus.kubeStateMetrics.global.imagePullSecrets .imagePullSecrets) }}
  {{- if eq (typeOf .) "map[string]interface {}" }}
- {{ toYaml . | trim }}
  {{- else }}
- name: {{ . }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
The image to use for kube-state-metrics
*/}}
{{- define "kube-state-metrics.image" -}}
{{- if .Values.prometheus.kubeStateMetrics.image.sha }}
{{- if .Values.prometheus.kubeStateMetrics.global.imageRegistry }}
{{- printf "%s/%s:%s@%s" .Values.prometheus.kubeStateMetrics.global.imageRegistry .Values.prometheus.kubeStateMetrics.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.image.tag) .Values.prometheus.kubeStateMetrics.image.sha }}
{{- else }}
{{- printf "%s/%s:%s@%s" .Values.prometheus.kubeStateMetrics.image.registry .Values.prometheus.kubeStateMetrics.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.image.tag) .Values.prometheus.kubeStateMetrics.image.sha }}
{{- end }}
{{- else }}
{{- if .Values.prometheus.kubeStateMetrics.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.prometheus.kubeStateMetrics.global.imageRegistry .Values.prometheus.kubeStateMetrics.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.image.tag) }}
{{- else }}
{{- printf "%s/%s:%s" .Values.prometheus.kubeStateMetrics.image.registry .Values.prometheus.kubeStateMetrics.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.image.tag) }}
{{- end }}
{{- end }}
{{- end }}

{{/*
The image to use for kubeRBACProxy
*/}}
{{- define "kubeRBACProxy.image" -}}
{{- if .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.sha }}
{{- if .Values.prometheus.kubeStateMetrics.global.imageRegistry }}
{{- printf "%s/%s:%s@%s" .Values.prometheus.kubeStateMetrics.global.imageRegistry .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.tag) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.sha }}
{{- else }}
{{- printf "%s/%s:%s@%s" .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.registry .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.tag) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.sha }}
{{- end }}
{{- else }}
{{- if .Values.prometheus.kubeStateMetrics.global.imageRegistry }}
{{- printf "%s/%s:%s" .Values.prometheus.kubeStateMetrics.global.imageRegistry .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.tag) }}
{{- else }}
{{- printf "%s/%s:%s" .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.registry .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.repository (default (printf "v%s" .Chart.AppVersion) .Values.prometheus.kubeStateMetrics.kubeRBACProxy.image.tag) }}
{{- end }}
{{- end }}
{{- end }}

##### DCGM EXPORTER #####

{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "dcgm-exporter.name" -}}
{{- default .Chart.Name .Values.dcgmExporter.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "dcgm-exporter.fullname" -}}
{{- if .Values.dcgmExporter.fullnameOverride -}}
{{- .Values.dcgmExporter.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.dcgmExporter.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}


{{/*
Allow the release namespace to be overridden for multi-namespace deployments in combined charts
*/}}
{{- define "dcgm-exporter.namespace" -}}
  {{- if .Values.dcgmExporter.namespaceOverride -}}
    {{- .Values.dcgmExporter.namespaceOverride -}}
  {{- else -}}
    {{- .Release.Namespace -}}
  {{- end -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "dcgm-exporter.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "dcgm-exporter.labels" -}}
helm.sh/chart: {{ include "dcgm-exporter.chart" . }}
{{ include "dcgm-exporter.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "dcgm-exporter.selectorLabels" -}}
app.kubernetes.io/name: {{ include "dcgm-exporter.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the service account to use
*/}}
{{- define "dcgm-exporter.serviceAccountName" -}}
{{- if .Values.dcgmExporter.serviceAccount.create -}}
    {{ default (include "dcgm-exporter.fullname" .) .Values.dcgmExporter.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.dcgmExporter.serviceAccount.name }}
{{- end -}}
{{- end -}}
