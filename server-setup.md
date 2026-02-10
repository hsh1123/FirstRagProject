# AWS 서버 구축 히스토리

> 서버: AWS EC2 (Ubuntu 22.04 LTS)
> 인스턴스: t3.medium ~ t3.large
> 접속: ssh -i "키페어.pem" ubuntu@<Elastic IP>

---

## 1. Docker 설치

```bash
# 패키지 업데이트
sudo apt update && sudo apt upgrade -y

# 리부트 하라길래 리부트 한번 진행함
sudo reboot

# Docker 설치
curl -fsSL https://get.docker.com | sudo sh

# 현재 유저에게 Docker 권한 부여
sudo usermod -aG docker $USER

# 재접속 후 확인
docker --version

# docker 그룹 세션 초기화
newgrp docker
```

## 2. 소스 코드 클론 및 Docker 빌드

```bash
# GitHub에서 소스 클론
git clone https://github.com/<본인계정>/firstRagProject.git
cd firstRagProject

# .env 파일 생성 (API 키 설정)
echo 'GOOGLE_API_KEY=여기에_실제_키' > .env

# Docker 이미지 빌드
docker build -t rag-app .

#정상 빌드 되었는지 확인
docker images

# 컨테이너 실행
docker run --env-file .env -p 8000:8000 rag-app
```

## 3. K3s 설치 (경량 쿠버네티스)

```bash
# 실행 중인 Docker 컨테이너 정지
docker ps
docker stop $(docker ps -q)

# K3s 설치
curl -sfL https://get.k3s.io | sh -

# 설치 확인 (Ready 상태인지 확인)
sudo kubectl get nodes

# 일반 유저도 kubectl 사용할 수 있도록 권한 설정
sudo chmod 644 /etc/rancher/k3s/k3s.yaml
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> ~/.bashrc
```

## 4. K8s 매니페스트 배포

```bash
# Docker 이미지를 K3s 컨테이너 런타임에 import
sudo docker save rag-app:latest | sudo k3s ctr images import -

# API 키를 K8s Secret으로 생성
kubectl create secret generic rag-secret \
  --from-literal=GOOGLE_API_KEY='여기에_실제_키'

# 매니페스트 적용 (GitHub push → git pull 후)
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# 배포 상태 확인
kubectl get pods
kubectl get svc

# 접속: http://<Elastic IP>:30080
```

## 5. Argo CD 설치

```bash
# Argo CD 네임스페이스 생성 및 설치
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Pod 전부 Running 될 때까지 대기 (1~2분)
kubectl get pods -n argocd -w

# Argo CD 웹 UI를 외부에서 접속할 수 있도록 NodePort로 변경
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort", "ports": [{"port": 443, "targetPort": 8080, "nodePort": 30443}]}}'

# 초기 admin 비밀번호 확인
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

# 접속: https://<Elastic IP>:30443
# ID: admin / PW: 위 명령어 출력값
```

## 6. Argo CD - GitHub 연동

### 웹 UI에서 진행

1. **Repository 연결**
   - Settings → Repositories → Connect Repo
   - Method: VIA HTTPS
   - Repository URL: https://github.com/<본인계정>/firstRagProject.git
   - (public 리포면 인증 불필요)

2. **Application 생성**
   - Applications → New App
   - Application Name: rag-app
   - Project: default
   - Sync Policy: Automatic
   - Repository URL: 위에서 연결한 리포
   - Path: k8s
   - Cluster URL: https://kubernetes.default.svc
   - Namespace: default
   - Create 클릭

## 7. ChromaDB 분리 배포 (StatefulSet + PVC)

```bash
# GitHub push 후 서버에서 pull
cd firstRagProject && git pull

# Docker 이미지 재빌드 (main.py 변경됨)
docker build -t rag-app .
sudo docker save rag-app:latest | sudo k3s ctr images import -

# ChromaDB 배포
kubectl apply -f k8s/chromadb-statefulset.yaml
kubectl apply -f k8s/chromadb-service.yaml

# ChromaDB Pod Running 확인
kubectl get pods -w

# RAG 앱 재배포
kubectl rollout restart deployment rag-app

# 전체 확인
kubectl get pods
kubectl get svc
```

## 8. Prometheus + Grafana 모니터링 설치

```bash
# Helm 설치
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# 모니터링 네임스페이스 생성
kubectl create namespace monitoring

# Prometheus + Grafana 스택 설치
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring

# Pod 전부 Running 될 때까지 대기
kubectl get pods -n monitoring -w

# Grafana 웹 UI를 외부에서 접속할 수 있도록 NodePort로 변경
kubectl patch svc monitoring-grafana -n monitoring -p '{"spec": {"type": "NodePort", "ports": [{"port": 80, "targetPort": 3000, "nodePort": 30300}]}}'

# 접속: http://<Elastic IP>:30300
# ID: admin / PW: prom-operator
```
