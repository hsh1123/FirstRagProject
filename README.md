# RAG (Retrieval-Augmented Generation) 파이프라인 프로젝트

## 프로젝트 개요

이 프로젝트는 Retrieval-Augmented Generation (RAG) 기술을 사용하여 문서 기반의 질의응답(Q&A)을 수행하는 파이프라인을 구현합니다. 사용자가 질문을 입력하면, 프로젝트는 미리 인덱싱된 문서에서 관련 정보를 검색하고, 이 정보를 바탕으로 대규모 언어 모델(LLM)이 답변을 생성합니다.

## 프로젝트 구조

```
firstRagProject/
├── .env                  # 환경 변수 파일 (API 키 등)
├── dummy_document.txt    # RAG의 기반이 되는 텍스트 문서
├── rag_pipeline.py       # RAG 파이프라인 실행 스크립트
├── requirements.txt      # 프로젝트 의존성 목록
├── try-1.txt             # (디버깅 기록)
├── try-2.txt             # (디버깅 기록)
└── .venv/                # 파이썬 가상 환경
```

## 설정 방법

1.  **파이썬 설치**:
    *   이 프로젝트는 파이썬 3.11 버전에서 테스트되었습니다. 시스템에 파이썬 3.11이 설치되어 있는지 확인하세요.

2.  **가상 환경 생성 및 활성화**:
    *   프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 가상 환경을 생성하고 활성화합니다.
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```

3.  **의존성 설치**:
    *   다음 명령어를 사용하여 `requirements.txt` 파일에 명시된 라이브러리를 설치합니다.
        ```bash
        pip install -r requirements.txt
        ```

4.  **API 키 설정**:
    *   `.env` 파일을 생성하고, 파일 내에 Google API 키를 다음과 같이 추가합니다.
        ```
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
        ```
        `YOUR_GOOGLE_API_KEY` 부분을 실제 발급받은 API 키로 교체하세요.

## 실행 방법

1.  **RAG 파이프라인 실행**:
    *   다음 명령어를 사용하여 `rag_pipeline.py` 스크립트를 실행합니다.
        ```bash
        python rag_pipeline.py
        ```

2.  **질의응답**:
    *   스크립트가 실행되면 "You can now ask questions. Type 'exit' to quit." 메시지가 나타납니다.
    *   "Question: " 프롬프트에 질문을 입력하고 Enter 키를 누르면, RAG 파이프라인이 `dummy_document.txt` 파일의 내용을 기반으로 답변을 생성합니다.
    *   프로그램을 종료하려면 'exit'를 입력하세요.

## RAG 파이프라인 설명

`rag_pipeline.py` 스크립트는 다음과 같은 단계로 RAG 파이프라인을 구성하고 실행합니다.

1.  **인덱싱 (Indexing)**:
    *   `dummy_document.txt` 파일을 로드합니다.
    *   문서를 의미 있는 작은 조각(chunk)으로 분할합니다.
    *   `GoogleGenerativeAIEmbeddings` 모델을 사용하여 각 조각을 벡터 임베딩으로 변환합니다.
    *   `Chroma` 벡터 데이터베이스에 텍스트 조각과 해당 벡터를 저장하고 인덱싱합니다. 이 과정은 `./chroma_db` 디렉토리에 저장되어 재사용됩니다.

2.  **검색 (Retrieval)**:
    *   사용자의 질문이 입력되면, 임베딩 모델을 사용하여 질문을 벡터로 변환합니다.
    *   벡터 데이터베이스에서 질문 벡터와 가장 유사한(관련성 높은) 문서 조각들을 검색합니다.

3.  **생성 (Generation)**:
    *   `ChatGoogleGenerativeAI` (LLM) 모델을 사용하여 답변을 생성합니다.
    *   이때, 검색된 문서 조각들을 컨텍스트(context)로 함께 제공하여, LLM이 컨텍스트에 기반한 정확하고 관련성 높은 답변을 생성하도록 합니다.
    *   `ChatPromptTemplate`을 사용하여 LLM에게 컨텍스트와 질문을 명확한 형식으로 전달합니다.
