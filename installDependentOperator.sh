#!/bin/bash

set -e

echo "📦 Installing Serverless Operator in openshift-serverless..."
oc apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: openshift-serverless
---
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: serverless-operator-group
  namespace: openshift-serverless
spec: {}
---
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: serverless-operator
  namespace: openshift-serverless
spec:
  channel: stable
  name: serverless-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

echo "📦 Installing Service Mesh Operator in openshift-operators..."
oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: servicemeshoperator
  namespace: openshift-operators
  labels:
    operators.coreos.com/servicemeshoperator.openshift-operators: ""
spec:
  channel: stable
  installPlanApproval: Automatic
  name: servicemeshoperator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

echo "📦 Installing Authorino Operator in openshift-operators..."
oc apply -f - <<EOF
apiVersion: operators.coreos.com/v1alpha1
kind: Subscription
metadata:
  name: authorino-operator
  namespace: openshift-operators
  labels:
    operators.coreos.com/authorino-operator.openshift-operators: ""
spec:
  channel: stable
  installPlanApproval: Automatic
  name: authorino-operator
  source: redhat-operators
  sourceNamespace: openshift-marketplace
EOF

wait_for_operator() {
  local name="$1"
  local namespace="$2"
  local timeout=600  # in seconds
  local interval=2
  local waited=0

  echo "⏳ Waiting for $name to finish installing in $namespace (timeout: ${timeout}s)..."
  until oc get csv -n "$namespace" | grep "$name" | grep Succeeded; do
    if [ "$waited" -ge "$timeout" ]; then
      echo "❌ Timeout waiting for $name in $namespace after ${timeout}s"
      return 1
    fi
    echo "🔄 $name still installing... checked at ${waited}s"
    sleep "$interval"
    waited=$((waited + interval))
  done

  echo "✅ $name installation complete!"
}

wait_for_operator "serverless-operator" "openshift-serverless" || exit 1
wait_for_operator "servicemeshoperator" "openshift-operators" || exit 1
wait_for_operator "authorino-operator" "openshift-operators" || exit 1


echo "✅ All operators set to install using the 'stable' channel with latest versions."

