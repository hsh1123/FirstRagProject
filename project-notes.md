# RAG 프로젝트 전체 정리

---

## 1. 프로젝트 개요

### 파일 구조

```
firstRagProject/
├── .env                          # 비밀 설정 (API 키) - Git 제외
├── .gitignore                    # Git에서 제외할 파일 목록
├── .dockerignore                 # Docker 빌드 시 제외할 파일 목록
├── Dockerfile                    # Docker 이미지 빌드 설정
├── requirements.txt              # 필요한 라이브러리 목록
├── dummy_document.txt            # RAG가 참고하는 문서 (지식 베이스)
├── rag_pipeline.py               # CLI 버전 (터미널에서 실행)
├── main.py                       # FastAPI 서버 버전 (웹에서 실행)
├── static/
│   └── index.html                # 챗봇 UI (브라우저 화면)
├── k8s/
│   ├── deployment.yaml           # RAG 앱 배포 설정
│   ├── service.yaml              # 외부 접속 설정 (NodePort)
│   ├── chromadb-statefulset.yaml # ChromaDB 배포 설정
│   └── chromadb-service.yaml     # ChromaDB 내부 통신 설정
├── chroma_db/                    # 벡터 DB (자동 생성됨) - Git 제외
├── .venv/                        # 파이썬 라이브러리 저장소 - Git 제외
├── masterplan.md                 # 8주 로드맵
├── server-setup.md               # 서버 구축 히스토리
└── project-notes.md              # 이 파일
```

### 사용 기술 스택

| 기술 | 역할 |
|------|------|
| Python 3.11.8 | 전체 백엔드 언어 |
| FastAPI | 웹 서버 프레임워크 (API 제공) |
| LangChain | RAG 파이프라인 조립 도구 |
| ChromaDB 1.4.1 | 벡터 데이터베이스 (문서 저장/검색) |
| Google Gemini | LLM (gemini-2.0-flash) + 임베딩 (gemini-embedding-001) |
| HTML/JS | 챗봇 UI |
| Docker | 앱 컨테이너화 |
| K3s | 경량 쿠버네티스 |
| Argo CD | GitOps 자동 배포 |
| Prometheus | 메트릭 수집/저장 |
| Grafana | 모니터링 시각화 |

---

## 2. RAG (Retrieval-Augmented Generation) 설명

### RAG란?

일반 LLM에게 "회사 내부 문서에 뭐라고 써있어?" 하면 모른다. 학습 데이터에 없으니까.
RAG는 LLM에게 **커닝페이퍼를 쥐어주는 것**이다.

```
[일반 LLM]
질문 → LLM → 답변 (모르면 헛소리함)

[RAG]
질문 → 내 문서에서 관련 내용 검색 → 검색 결과 + 질문을 LLM에 전달 → 답변
```

### 동작 순서 (3단계)

#### 1단계: 인덱싱 (서버 시작 시 1회)

```
dummy_document.txt
    ↓
텍스트를 작은 조각(chunk)으로 분할
    ↓
각 조각을 숫자 벡터로 변환 (임베딩)
    ↓
chroma_db에 저장
```

"RAG는 Retrieval-Augmented..." 같은 문장을 [0.12, -0.34, 0.56, ...] 같은 숫자 배열로 바꿔서 저장한다.
의미가 비슷한 문장끼리 숫자도 비슷해져서 검색이 가능해진다.

#### 2단계: 검색 (질문할 때마다)

```
"RAG가 뭐야?"
    ↓
질문도 벡터로 변환
    ↓
chroma_db에서 비슷한 벡터를 가진 문서 조각 찾기
    ↓
관련 문서 조각 반환
```

#### 3단계: 생성

```
프롬프트:
"아래 내용을 참고해서 답변해:
 [검색된 문서 조각]
 질문: RAG가 뭐야?"
    ↓
Gemini LLM이 답변 생성
```

### 토큰 비용이 발생하는 시점

| 단계 | 토큰 비용 | 횟수 |
|------|-----------|------|
| 인덱싱 (임베딩) | 발생 | 최초 1회 (서버 시작 시) |
| 질문 임베딩 | 발생 | 질문할 때마다 (아주 적음, 한 문장 수십 토큰) |
| 벡터 검색 | 없음 | 로컬 DB에서 수학 연산 |
| LLM 답변 생성 | 발생 | 질문할 때마다 (비용의 대부분) |

한번 인덱싱하고 나면 chroma_db를 삭제하지 않는 한 재인덱싱 비용은 없다.

---

## 3. 벡터 DB (ChromaDB) 구조

### 저장소 파일

```
chroma_db/
├── chroma.sqlite3          # 메타데이터 + 문서 텍스트 (SQLite)
└── <uuid>/                 # 벡터 인덱스 파일 (HNSW 알고리즘)
    ├── header.bin           # 인덱스 설정 정보 (차원 수, 거리 함수 등)
    ├── data_level0.bin      # 실제 벡터 데이터 (숫자 배열)
    ├── link_lists.bin       # 벡터 간 연결 그래프 (검색 경로)
    └── length.bin           # 각 벡터의 연결 리스트 길이 정보
```

### 각 chunk에 저장되는 정보

```
┌─────────────────────────────────────────┐
│  id: "9fe61d1e-..."                     │  ← 고유 식별자
│  document: "RAG는 Retrieval-Aug..."      │  ← 원본 텍스트 조각
│  embedding: [0.12, -0.34, 0.56, ...]    │  ← 벡터 (숫자 배열)
│  metadata: {source: "dummy_document.txt"}│  ← 출처 정보
└─────────────────────────────────────────┘
```

### HNSW 검색 원리

```
모든 벡터를 일일이 비교하면 느림 (O(n))
    ↓
대신 벡터들을 그래프로 연결해놓고
가까운 이웃끼리 링크를 만들어둠
    ↓
질문 벡터가 들어오면 그래프를 따라가며
빠르게 가장 비슷한 벡터를 찾음 (O(log n))
```

data_level0.bin이 벡터 자체, link_lists.bin이 그래프 연결 정보.
chroma.sqlite3에는 원본 텍스트와 메타데이터가 따로 저장.

---

## 4. 코드 흐름

### main.py (FastAPI 서버)

```
서버 시작 (python main.py)
    ↓
lifespan() 실행 → ChromaDB 연결, 인덱싱, RAG 체인 준비
    ↓
http://localhost:8000 에서 대기
    ↓
브라우저 접속 → index.html 반환
    ↓
사용자가 질문 입력 → POST /chat 호출
    ↓
chat() 함수 → retrieval_chain.invoke() → 답변 반환
```

### static/index.html (프론트)

```
사용자가 질문 입력 → 전송 버튼 클릭
    ↓
fetch('/chat', {message: "질문"})  ← 서버에 HTTP 요청
    ↓
서버 응답 {answer: "답변"} 수신
    ↓
화면에 답변 표시
```

### API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| GET / | 챗봇 UI 페이지 |
| POST /chat | {"message": "질문"} → {"answer": "답변"} |

### CLI vs FastAPI 차이

| | CLI (rag_pipeline.py) | FastAPI (main.py) |
|---|---|---|
| 질문 입력 | 터미널 input() | HTTP POST 요청 |
| 응답 | print() 출력 | JSON 응답 |
| 접근 방식 | 로컬 터미널만 | 브라우저/프론트에서 호출 |
| 배포 | 불가 | Docker/K8s 배포 가능 |

---

## 5. 겪었던 이슈 및 해결

### Python 버전 문제

- Python 3.14는 chromadb/torch 등 미지원
- .venv가 3.14로 만들어져 있었음 (시스템은 3.11.8)
- 해결: .venv 삭제 후 3.11.8로 재생성

### 라이브러리 버전 충돌

| 문제 | 원인 | 해결 |
|------|------|------|
| PydanticImportError | chromadb 0.3.x가 pydantic v2와 비호환 | chromadb 1.4.1로 업그레이드 |
| pydantic v1 다운그레이드 실패 | langchain-core가 pydantic v2 필수 | 전체 최신 버전으로 통일 |
| langchain.chains import 실패 | 최신 langchain에서 langchain-classic으로 이동 | import 경로 변경 |
| SSL 인증서 오류 | chromadb가 sentence-transformers 다운로드 시 | Python 버전 변경으로 해결 |
| 한글 인코딩 깨짐 | Windows 콘솔 인코딩 문제 | print문 영어로 변경 |

### deprecated 모델

| 변경 전 | 변경 후 |
|---------|---------|
| embedding-001 | gemini-embedding-001 |
| gemini-pro | gemini-2.0-flash |
| vectordb.persist() | 제거 (자동 저장) |
| langchain_community.vectorstores.Chroma | langchain_chroma.Chroma |
| convert_system_message_to_human=True | 제거 (불필요) |

### API 키 유출

- .env 파일이 Git에 커밋되어 있었음
- Google이 감지하고 키 차단 ("Your API key was reported as leaked")
- 해결: .gitignore 추가, Git 추적 해제, 키 재발급

### 무료 API 할당량 초과

- free tier quota가 limit: 0으로 표시됨
- 해결: 결제가 연결된 Google Cloud 프로젝트에서 API 키 발급

---

## 6. Docker

### Dockerfile 설명

```dockerfile
FROM python:3.11-slim          # Python 3.11 경량 리눅스 이미지
WORKDIR /app                   # 컨테이너 내 작업 디렉토리
COPY requirements.txt .        # 의존성 파일 복사
RUN pip install ...            # 라이브러리 설치
COPY main.py .                 # 앱 코드 복사
COPY dummy_document.txt .      # 문서 복사
COPY static/ static/           # UI 복사
EXPOSE 8000                    # 8000번 포트 사용 선언
CMD ["uvicorn", ...]           # 컨테이너 시작 시 실행할 명령
```

### .dockerignore

.venv, .env, .git 등 이미지에 들어가면 안 되는 파일 제외.
특히 .env는 API 키가 이미지에 포함되면 안 되므로 반드시 제외.
실행 시 환경변수로 주입한다.

### Docker 명령어

```bash
docker build -t rag-app .                    # 이미지 빌드
docker run --env-file .env -p 8000:8000 rag-app  # 컨테이너 실행
docker images                                # 이미지 목록 확인
docker ps                                    # 실행 중인 컨테이너 확인
docker stop $(docker ps -q)                  # 모든 컨테이너 정지
```

### apt vs curl 설치 차이

| 방법 | 버전 | 특징 |
|------|------|------|
| curl -fsSL https://get.docker.com \| sudo sh | 최신 버전 | Docker 공식 스크립트 |
| sudo apt install docker.io | Ubuntu 저장소 버전 | 약간 구버전, 안정적 |

curl 스크립트가 하는 일도 결국 Docker 공식 apt 저장소를 등록하고 apt install하는 것.

### curl -fsSL 옵션 의미

| 옵션 | 의미 |
|------|------|
| -f | 서버 에러 시 조용히 실패 |
| -s | 진행률 표시 안 함 (silent) |
| -S | 에러 메시지는 표시 |
| -L | 리다이렉트 따라감 |

---

## 7. K3s (경량 쿠버네티스)

### K3s란?

쿠버네티스(K8s)의 경량 버전. 컨테이너를 관리/실행하는 플랫폼.

```
docker run으로 직접 실행 (수동)
    vs
쿠버네티스가 컨테이너 관리 (자동 재시작, 스케일링, 롤링 업데이트)
```

### K8s 리소스 관계도

```
Service (svc)
  └── 외부 트래픽을 Pod로 연결 (30080 포트)

Deployment (deploy)
  └── "Pod를 몇 개, 어떤 이미지로 만들지" 정의
      └── ReplicaSet (rs)
          └── 실제 Pod를 생성/관리
              ├── Pod 1 (rag-app-xxxxx)
              ├── Pod 2 (rag-app-yyyyy)
              └── Pod 3 (rag-app-zzzzz)
```

| 리소스 | 역할 |
|--------|------|
| Service (svc) | 외부 → Pod 트래픽 라우팅. 로드밸런서 역할 |
| Deployment (deploy) | Pod 배포 전략 정의 |
| ReplicaSet (rs) | Pod 개수 유지. Pod 죽으면 자동 재생성 |
| StatefulSet | DB 같은 상태 유지가 필요한 앱용. 고정 이름, 순서 보장 |
| PVC (PersistentVolumeClaim) | 디스크 공간 요청. Pod 죽어도 데이터 유지 |
| ControllerRevision | StatefulSet의 버전 이력 (롤백용) |
| Secret | API 키 같은 민감 정보 저장 |

### Docker → K3s 이미지 전달

K3s는 Docker와 별도의 컨테이너 런타임(containerd)을 사용한다.

```
docker images       → Docker 런타임의 이미지 저장소
k3s ctr images list → K3s(containerd) 런타임의 이미지 저장소
```

둘은 분리되어 있어서 Docker로 빌드한 이미지를 K3s 쪽으로 옮겨줘야 한다.

```bash
sudo docker save rag-app:latest | sudo k3s ctr images import -
```

### Service 타입

| 타입 | 용도 |
|------|------|
| NodePort (30080) | 외부 → RAG 앱 접속 |
| ClusterIP (None) / Headless | K8s 내부 전용 통신 (ChromaDB) |

### 트래픽 흐름

```
브라우저 http://<IP>:30080
    ↓
Service (NodePort 30080)
    ↓ (로드밸런싱)
Pod 1, Pod 2, Pod 3 중 하나의 :8000으로 전달
    ↓
Pod 내부에서 ChromaDB Service → ChromaDB Pod로 통신
```

### ReplicaSet이 여러 개인 이유

K8s가 롤링 업데이트할 때마다 새 ReplicaSet을 만들고, 이전 것은 Pod 수만 0으로 줄여서 보관.
롤백할 때 이전 ReplicaSet을 다시 살릴 수 있다.

### Pod가 죽는 케이스

| 원인 | 상황 |
|------|------|
| OOM (메모리 부족) | 요청 몰리면서 메모리 초과 → K8s가 강제 종료 |
| 앱 에러 | 코드 버그로 프로세스 크래시 |
| 노드 장애 | 서버 자체가 다운 |
| 배포 중 | 새 버전 배포 시 기존 Pod 종료 → 새 Pod로 교체 |
| 리소스 부족 | CPU/메모리 제한에 걸려서 eviction |
| 헬스체크 실패 | 앱이 응답 안 하면 K8s가 비정상 판단 후 재시작 |

Pod가 죽으면 ReplicaSet이 자동으로 새 Pod를 생성. replicas를 여러 개 두는 게 무중단 운영의 핵심.

### 롤링 업데이트 (버전 업데이트 시)

```
시작:  Pod1(v1)  Pod2(v1)  Pod3(v1)
단계1: Pod1(v1)  Pod2(v1)  Pod4(v2) ← 새 Pod 먼저 생성
단계2: Pod1(v1)  Pod4(v2)  Pod5(v2) ← 기존 Pod 하나씩 교체
완료:  Pod4(v2)  Pod5(v2)  Pod6(v2)
```

- 기존 Pod는 새 Pod가 정상 뜰 때까지 살아있음
- 짧은 API 호출(채팅 질문/답변)은 거의 영향 없음
- Pod 교체 찰나에 해당 Pod로 요청이 들어가면 실패할 수 있음 (극히 드묾)

### 롤백

잘못된 배포 시 기본적으로 자동 롤백하지 않음.
새 Pod가 에러로 못 뜨면 실패 상태로 남지만, 기존 Pod는 살아있어서 서비스는 유지.

```bash
kubectl rollout undo deployment rag-app    # 수동 롤백
kubectl rollout history deployment rag-app # 배포 이력 확인
```

### Resource Limits

```yaml
resources:
  requests:          # 최소 보장 리소스
    cpu: "100m"      # CPU 0.1코어
    memory: "256Mi"  # 메모리 256MB
  limits:            # 최대 사용 가능 리소스
    cpu: "500m"      # CPU 0.5코어
    memory: "512Mi"  # 메모리 512MB
```

| 항목 | requests | limits |
|------|----------|--------|
| 역할 | "최소 이만큼은 확보해줘" | "이 이상은 쓰지 마" |
| CPU 초과 시 | - | 스로틀링 (느려짐) |
| 메모리 초과 시 | - | Pod 강제 종료 (OOM Kill) |

---

## 8. ChromaDB K8s 분리 배포

### 분리 이유

기존에는 각 Pod 안에 chroma_db/ 파일이 있었다.

```
문제 1: Pod마다 DB가 따로 → 3개 Pod = 3번 임베딩 = 비용 3배
문제 2: Pod 죽으면 데이터 소실 → 매번 재인덱싱
문제 3: 스케일링 불가 → Pod 올라갈 때마다 반복
```

### 분리 후 구조

```
Pod 1 ──┐
Pod 2 ──┼──→ ChromaDB (별도 StatefulSet + PVC)
Pod 3 ──┘         └── 디스크에 영구 저장
```

- DB 1개를 모든 Pod가 공유
- Pod가 죽어도 데이터 유지 (PVC)
- 인덱싱 1번이면 끝

### PVC (PersistentVolumeClaim)

ChromaDB 데이터를 저장할 디스크 공간 요청서.
Pod가 죽고 다시 올라와도 임베딩 데이터가 살아있다.

```
StatefulSet (chromadb)
  ├── ControllerRevision  ← 설정 변경 이력 (롤백용)
  ├── PVC (5Gi)           ← 디스크 (Pod 죽어도 데이터 유지)
  └── Pod (chromadb-0)    ← 실제 컨테이너
```

---

## 9. Argo CD (GitOps 자동 배포)

### Argo CD란?

GitHub의 YAML을 감시하다가 변경되면 자동으로 K8s에 배포하는 도구.

### 배포 흐름

```
코드 수정 → GitHub push
    ↓
Argo CD가 1~3분 내 자동 감지
    ↓
K8s에 변경사항 자동 반영 (Sync)
```

### 테스트 방법

deployment.yaml에서 replicas 변경 → GitHub push → Pod 수 자동 변경 확인.

### Application 상태

| 상태 | 의미 |
|------|------|
| Synced + Healthy | 정상 |
| OutOfSync | Sync 필요 |
| Degraded | Pod에 문제 있음 |

---

## 10. Prometheus + Grafana (모니터링)

### 역할 차이

| | Prometheus | Grafana |
|--|-----------|---------|
| 역할 | 데이터 수집/저장 | 시각화/대시보드 |
| 비유 | CCTV 녹화기 | CCTV 모니터 |

```
서버/Pod → Prometheus가 메트릭 수집 → 저장
                                      ↓
                              Grafana가 읽어서 그래프로 보여줌
```

### Grafana 주요 대시보드

| 대시보드 | 검색 키워드 | 보여주는 것 |
|----------|------------|------------|
| Node Exporter / Nodes | Nodes | 서버 CPU/메모리/디스크/네트워크 |
| Kubernetes / Compute Resources / Namespace (Pods) | Pods | Pod별 리소스 사용량 |
| Kubernetes / Compute Resources / Cluster | Cluster | 클러스터 전체 요약 |

### 실용적으로 보는 포인트

```
메모리 사용량이 limits(512Mi)에 가까움 → limits 올려야 함
CPU가 requests(100m)보다 훨씬 높음    → requests 올려야 함
노드 메모리가 90% 이상               → 인스턴스 스펙 업 또는 Pod 줄이기
```

### Resource Limits와 Grafana 관계

```
deployment.yaml의 resources  →  K8s가 Pod에 제한 적용 (실제 제한)
                                    ↓
                              Prometheus가 사용량 수집
                                    ↓
                              Grafana가 시각화해서 보여줌 (보여주는 역할만)
```

---

## 11. AWS EC2 관련

### 서버 스펙

| 항목 | 값 |
|------|-----|
| 인스턴스 | t3.medium ~ t3.large |
| OS | Ubuntu 22.04 LTS |
| Elastic IP | 할당 (서버 Stop/Start 해도 IP 유지) |

### 비용

| 상태 | 비용 |
|------|------|
| 상시 운영 (t3.large) | ~$65/월 |
| 작업할 때만 Start (하루 2시간) | ~$5~10/월 |
| Stop 상태 | EBS($2) + Elastic IP($3.6) ≈ $6/월 |

### Stop 시 동작

| 항목 | Stop 시 |
|------|---------|
| 인스턴스 비용 | 과금 중지 |
| EBS (디스크) | 계속 과금 (~$2/월) |
| 퍼블릭 IP (Elastic IP 없으면) | 해제됨 (바뀜) |
| Elastic IP (연결된 상태) | 무료 |
| Elastic IP (Stop 상태) | ~$3.6/월 |
| 데이터 | 유지 |

### 보안 그룹 포트

| 포트 | 용도 |
|------|------|
| 22 | SSH |
| 80 | HTTP |
| 443 | HTTPS |
| 6443 | K3s API |
| 8000 | RAG 앱 (Docker 직접 실행 시) |
| 8080 | Argo CD |
| 30000-32767 | K8s NodePort (범위로 입력) |

---

## 12. 운영 중인 서비스 포트 정리

| 포트 | 서비스 | 접속 URL |
|------|--------|----------|
| 30080 | RAG 챗봇 앱 | http://\<IP\>:30080 |
| 30300 | Grafana 모니터링 | http://\<IP\>:30300 |
| 30443 | Argo CD 배포 관리 | https://\<IP\>:30443 |

---

## 13. 자주 쓰는 명령어

```bash
# Pod 상태 확인
kubectl get pods
kubectl get pods -n argocd
kubectl get pods -n monitoring

# 서비스 확인
kubectl get svc

# Pod 상세 정보 (에러 확인)
kubectl describe pod <Pod이름>

# Pod 로그
kubectl logs <Pod이름>

# 배포 재시작
kubectl rollout restart deployment rag-app

# 롤백
kubectl rollout undo deployment rag-app

# 시스템 메모리 확인
free -h

# Docker 이미지 K3s로 import
sudo docker save rag-app:latest | sudo k3s ctr images import -
```

---

## 14. 향후 고도화 방향 (참고)

### 앱 고도화

- 인제스션 파이프라인: POST /ingest API로 파일 업로드 → 자동 인덱싱
- 여러 파일 포맷 지원 (PDF, Excel, PPT, Word)
- 대화 히스토리 (ConversationalRetrievalChain)
- 출처 표시 ("이 내용은 00.pdf 3페이지에서 가져왔습니다")
- 스트리밍 응답 (ChatGPT처럼 한 글자씩)
- 검색 품질 개선 (Hybrid Search, Re-ranking, Multi-query)
