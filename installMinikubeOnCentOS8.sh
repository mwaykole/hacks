#!/bin/bash
This script installs minikube on centos 8
set -e 

echo "Adding usernanme "
username="test" #enter-username
password="1" #enter-password
# Adding user
adduser "$username"
# Setting password
echo "$password" | passwd "$username" --stdin

sudo echo """$username ALL=(ALL) ALL
$username ALL=(ALL) NOPASSWD: /usr/bin/podman""">>/etc/sudoers

sudo echo """[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-x86_64
enabled=1
gpgcheck=0
repo_gpgcheck=0
""" > /etc/yum.repos.d/kubernetes.repo
# Adding port permanently

sudo firewall-cmd --permanent --add-port=6443/tcp
sudo firewall-cmd --permanent --add-port=2379-2380/tcp 
sudo firewall-cmd --permanent --add-port=10250/tcp 
sudo firewall-cmd --permanent --add-port=10251/tcp 
sudo firewall-cmd --permanent --add-port=10252/tcp 
sudo firewall-cmd --permanent --add-port=10255/tcp 
sudo firewall-cmd --reload

sudo setenforce 0
sudo sed -i 's/^SELINUX=enforcing$/SELINUX=permissive/g' /etc/selinux/config 
sudo sed -i '/swap/d' /etc/fstab ; sudo swapoff -a 



curl -O https://storage.googleapis.com/minikube/releases/latest/minikube-latest.x86_64.rpm ;sudo dnf install -y kubectl
rpm -ivh minikube-latest.x86_64.rpm

runuser -l test -c "minikube start --driver=podman --container-runtime=cri-o" 

runuser -l test -c "minikube status"
