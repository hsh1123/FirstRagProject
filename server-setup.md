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

# 컨테이너 실행
docker run --env-file .env -p 8000:8000 rag-app
```
