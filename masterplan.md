# RAG 프로젝트 마스터플랜 (8주 로드맵)

> 일일 1~2시간 투자 기준

---

## 1-2주차: 환경 구축 및 Hello RAG

- [ ] Windows 개발 환경 세팅 (Poetry, Python)
- [ ] 원격 리눅스 서버에 K3s 설치 및 로컬 윈도우와 연결 (kubeconfig)
- [ ] FastAPI를 활용한 기본 RAG API (LangChain 연동) 개발

## 3-4주차: 도커라이징 및 Argo CD 배포

- [ ] 애플리케이션 Docker 이미지 빌드 및 Docker Hub 푸시
- [ ] 원격 서버에 Argo CD 설치 및 GitHub 리포지토리 연동
- [ ] YAML 매니페스트 작성을 통한 첫 번째 K8s 배포 성공

## 5-6주차: 데이터 저장소 및 스테이트풀셋 (StatefulSet)

- [ ] 벡터 DB (Qdrant/ChromaDB)를 K8s에 배포
- [ ] 데이터 영속성을 위한 PV/PVC 설정 및 DB 연결
- [ ] 대량의 문서 데이터를 처리하는 인제스션(Ingestion) 파이프라인 구축

## 7-8주차: 모니터링 및 프로젝트 완결

- [ ] Prometheus & Grafana 설치 및 대시보드 구성
- [ ] AI 응답 속도 및 서버 리소스 사용량 최적화 (Resource Limits 설정)
