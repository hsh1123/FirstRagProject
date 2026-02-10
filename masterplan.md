# RAG 프로젝트 마스터플랜 (8주 로드맵)

> 일일 1~2시간 투자 기준

---

## 1-2주차: 환경 구축 및 Hello RAG ✅

- [x] Windows 개발 환경 세팅 (Python 3.11.8, venv)
- [x] 원격 리눅스 서버에 K3s 설치 및 로컬 윈도우와 연결 (kubeconfig)
- [x] FastAPI를 활용한 기본 RAG API (LangChain 연동) 개발

### 진행 내역
- Python 3.14 → 3.11.8로 venv 재생성 (라이브러리 호환성 문제 해결)
- chromadb 0.3.23 → 1.4.1 업그레이드 (pydantic v2 충돌 해소)
- deprecated 모델 교체: embedding-001 → gemini-embedding-001, gemini-pro → gemini-2.0-flash
- Chroma import를 langchain_community → langchain_chroma로 변경
- vectordb.persist() 제거 (최신 ChromaDB 자동 저장)
- .gitignore 추가 및 .env, chroma_db Git 추적 해제
- 유출된 API 키 폐기 후 유료 프로젝트 키로 교체
- FastAPI 서버(main.py) + 챗봇 UI(static/index.html) 구축
- AWS EC2 서버 생성 완료 (Elastic IP 할당)

---

## 3-4주차: 도커라이징 및 Argo CD 배포 ✅

- [x] 애플리케이션 Docker 이미지 빌드
- [x] 원격 서버에 Argo CD 설치 및 GitHub 리포지토리 연동
- [x] YAML 매니페스트 작성을 통한 첫 번째 K8s 배포 성공

### 진행 내역
- AWS EC2에 Docker 설치 및 rag-app 이미지 빌드
- K3s 설치, kubectl 권한 설정
- K8s Deployment + Service (NodePort 30080) 매니페스트 작성
- Docker 이미지를 K3s containerd로 import
- API 키를 K8s Secret으로 관리
- Argo CD 설치 (NodePort 30443)
- Argo CD ↔ GitHub 리포 연동, Automatic Sync 설정
- replicas 변경으로 자동 배포 테스트 성공

---

## 5-6주차: 데이터 저장소 및 스테이트풀셋 (StatefulSet) ✅

- [x] 벡터 DB (ChromaDB)를 K8s에 배포
- [x] 데이터 영속성을 위한 PV/PVC 설정 및 DB 연결
- [ ] 대량의 문서 데이터를 처리하는 인제스션(Ingestion) 파이프라인 구축

### 진행 내역
- ChromaDB를 StatefulSet으로 K8s에 분리 배포
- PVC 5Gi로 데이터 영속성 확보
- main.py를 HttpClient 방식으로 외부 ChromaDB 연결 수정
- Headless Service로 K8s 내부 통신 설정

---

## 7-8주차: 모니터링 및 프로젝트 완결 ✅

- [x] Prometheus & Grafana 설치 및 대시보드 구성
- [x] AI 응답 속도 및 서버 리소스 사용량 최적화 (Resource Limits 설정)

### 진행 내역
- Helm으로 kube-prometheus-stack 설치
- Grafana NodePort 30300으로 외부 접속 설정
- RAG 앱 + ChromaDB에 Resource Limits 설정 (CPU 500m, Memory 512Mi)
