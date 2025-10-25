# 에버노트 → 노션 마이그레이션 프로젝트 개발계획서

## 프로젝트 개요

### 목적
에버노트 노트북(.enex 파일)을 노션(Notion) 개인 페이지로 자동 마이그레이션하는 파이썬 프로그램 개발

### 데이터 현황 (실제 분석 결과)
- **소스 디렉토리**: `/Users/sunchulkim/evernote`
- **파일 개수**: 23개 .enex 파일
- **총 용량**: 약 450MB (최소 5KB ~ 최대 160MB)
- **총 노트 수**: 1,373개
- **총 리소스 수**: 1,574개 (이미지, PDF, Office 문서 등)

**주요 노트북**:
| 파일명 | 용량 | 노트 수 | 리소스 수 | 특이사항 |
|--------|------|---------|-----------|----------|
| 블로그_예전모음 | 160MB | 60 | 1,192 | 리소스 최다 |
| 책정리 | 116MB | 413 | 87 | 노트 최다 |
| 책 작성 | 56MB | 44 | 33 | - |
| 미국출장이야기 | 31MB | 80 | 25 | - |
| 블랙야크 | 29MB | 103 | 68 | - |

**리소스 포맷 분포**:
- **이미지**: JPEG (1,383개), PNG (160개), SVG (13개), WebP (1개)
- **문서**: PDF (11개), DOCX (1개), PPTX (1개)
- **텍스트**: Markdown (3개), Plain Text (1개)

### 기술 스택
- **언어**: Python 3.11+
- **주요 라이브러리**:
  - `notion-client` - Notion API 클라이언트
  - `lxml` 또는 `BeautifulSoup4` - ENEX(XML) 파싱
  - `python-dotenv` - 환경변수 관리
  - `tqdm` - 진행률 표시
  - `Pillow` - 이미지 처리 (필요시)
- **API**: Notion Official API (https://developers.notion.com/)

---

## 기술 분석

### 1. ENEX 파일 구조
ENEX는 Evernote의 XML 기반 백업 포맷입니다.

**기본 구조**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-export SYSTEM "http://xml.evernote.com/pub/evernote-export3.dtd">
<en-export>
  <note>
    <title>노트 제목</title>
    <content><![CDATA[<?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
      <en-note>
        <div>노트 본문 내용</div>
      </en-note>
    ]]></content>
    <created>20200101T120000Z</created>
    <updated>20200102T150000Z</updated>
    <tag>태그1</tag>
    <tag>태그2</tag>
    <note-attributes>
      <author>작성자</author>
      <source>web.clip</source>
      <source-url>https://example.com</source-url>
    </note-attributes>
    <resource>
      <data encoding="base64">...</data>
      <mime>image/png</mime>
      <width>800</width>
      <height>600</height>
      <resource-attributes>
        <file-name>screenshot.png</file-name>
        <source-url>https://example.com/image.png</source-url>
      </resource-attributes>
    </resource>
  </note>
  <note>...</note>
</en-export>
```

**주요 필드**:
- `<title>` - 노트 제목
- `<content>` - ENML(Evernote Markup Language) 형식의 본문
- `<created>`, `<updated>` - 생성/수정 시간
- `<tag>` - 태그 (다중 가능)
- `<resource>` - 첨부파일/이미지 (Base64 인코딩)
  - `<data encoding="base64">` - Base64 인코딩된 파일 데이터
  - `<mime>` - MIME 타입 (image/jpeg, image/png, application/pdf 등)
  - `<width>`, `<height>` - 이미지 크기 (이미지만 해당)
  - `<resource-attributes>` - 파일명, 원본 URL 등
- `<note-attributes>` - 메타데이터

**리소스-본문 연결**:
ENML 본문에서 리소스는 MD5 해시로 참조됩니다:
```xml
<en-media hash="34c08f36cde832639fdf3190a3786b4d" type="image/jpeg" />
```
이 해시는 리소스의 `<data>` Base64를 디코딩한 후 MD5 해시한 값과 일치합니다.

**실제 분석 결과**:
- 총 1,574개 리소스 중 **87.8%가 이미지** (JPEG/PNG)
- **PDF 11개, Office 문서 2개** 포함
- 단일 노트에 최대 수십 개 이미지 포함 가능
- SVG, WebP 등 다양한 포맷 지원 필요

**처리 과제**:
- ENML → Markdown 변환
- **1,574개 리소스 처리** (Base64 디코딩, 업로드)
- 리소스 MD5 해시 매칭
- 다양한 MIME 타입 처리 (9가지 포맷)
- 대용량 파일 처리 (160MB XML 파싱)
- 특수문자, HTML 엔티티 처리
- **블로그_예전모음.enex**: 단일 파일에 1,192개 리소스

### 2. Notion API 구조

**인증**:
- Internal Integration Token 방식
- API Key: `Bearer <token>` 헤더로 전달

**주요 엔드포인트**:
- `POST /v1/pages` - 페이지 생성
- `PATCH /v1/blocks/{block_id}/children` - 블록 추가
- `POST /v1/databases/{database_id}/query` - 데이터베이스 조회
- `POST /v1/files` - 파일 업로드 (외부 URL만 지원, Base64 직접 업로드 불가)

**블록 타입**:
- `paragraph` - 일반 텍스트
- `heading_1`, `heading_2`, `heading_3` - 제목
- `bulleted_list_item`, `numbered_list_item` - 리스트
- `to_do` - 체크박스
- `code` - 코드블록
- `image` - 이미지 (외부 URL 또는 Notion 호스팅)
- `file` - 파일 첨부 (PDF, Office 문서 등)
- `pdf` - PDF 임베드 (외부 URL만)
- `divider` - 구분선

**제약사항**:
- 블록당 최대 2000자
- API 요청 속도 제한: 초당 3회
- 이미지는 외부 URL 또는 Notion 자체 업로드만 가능 (Base64 직접 불가)
- 단일 API 호출로 최대 100개 블록 추가 가능

---

## 시스템 설계

### 아키텍처

```
┌─────────────────┐
│ ENEX Files      │
│ (.enex 26개)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ENEX Parser     │
│ - XML 파싱      │
│ - ENML → MD     │
│ - 메타데이터 추출│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Resource Handler│
│ - 이미지 추출    │
│ - Base64 디코딩 │
│ - 임시 저장     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notion Uploader │
│ - 이미지 업로드  │
│ - 페이지 생성    │
│ - 블록 추가     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Notion Workspace│
│ (개인 페이지)    │
└─────────────────┘
```

### 디렉토리 구조

```
evernote-to-notion/
├── .env                        # API 키, 설정
├── .env.example                # 환경변수 템플릿
├── .gitignore
├── requirements.txt
├── README.md
├── PROJECT_PLAN.md             # 이 문서
├── main.py                     # 메인 실행 스크립트
├── config.py                   # 설정 관리
├── app/
│   ├── __init__.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── enex_parser.py      # ENEX XML 파싱
│   │   └── enml_converter.py   # ENML → Markdown 변환
│   ├── notion/
│   │   ├── __init__.py
│   │   ├── client.py           # Notion API 클라이언트
│   │   ├── page_creator.py     # 페이지 생성
│   │   └── block_builder.py    # 블록 구성
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── image_handler.py    # 이미지 처리
│   │   └── file_manager.py     # 임시 파일 관리
│   └── utils/
│       ├── __init__.py
│       ├── logger.py           # 로깅
│       └── rate_limiter.py     # API 속도 제한 관리
├── scripts/
│   ├── test_enex_parse.py      # ENEX 파싱 테스트
│   ├── test_notion_api.py      # Notion API 연결 테스트
│   └── migrate_single.py       # 단일 파일 마이그레이션 (디버깅용)
├── data/
│   ├── temp/                   # 임시 이미지 저장
│   ├── logs/                   # 로그 파일
│   └── checkpoint/             # 진행 상황 체크포인트
└── tests/
    ├── __init__.py
    ├── test_parser.py
    ├── test_converter.py
    └── test_notion_client.py
```

---

## 개발 단계

### Phase 1: 환경 설정 및 기본 파싱 (1-2일)

**목표**: ENEX 파일 파싱 및 구조 분석

**작업**:
1. 프로젝트 초기화
   - 디렉토리 구조 생성
   - `requirements.txt` 작성
   - `.env.example` 작성
   - Git 저장소 초기화

2. ENEX 파서 개발
   - `enex_parser.py`: XML 파싱, 노트 목록 추출
   - 샘플 파일로 구조 분석 (작은 파일부터: `맛집.enex` 5KB)
   - 메타데이터 추출 (제목, 날짜, 태그)

3. 테스트 스크립트
   - `scripts/test_enex_parse.py`: 파싱 결과 확인
   - 전체 26개 파일에 대한 통계 수집 (노트 개수, 리소스 개수)

**체크포인트**:
- [ ] 모든 .enex 파일 파싱 성공
- [ ] 총 노트 개수, 태그 종류, 이미지 개수 통계 출력
- [ ] 대용량 파일(160MB) 파싱 성공

---

### Phase 2: ENML → Notion 블록 변환 (2-3일)

**목표**: Evernote Markup을 Notion 블록으로 변환

**작업**:
1. ENML 분석
   - ENML 태그 목록 파악 (`<div>`, `<span>`, `<en-todo>`, `<en-media>` 등)
   - HTML 유사 태그와 특수 태그 구분

2. Markdown 변환기 개발
   - `enml_converter.py`: ENML → Markdown 변환
   - 지원 요소:
     - 제목 (`<h1>` → `# Heading`)
     - 리스트 (`<ul>`, `<ol>`)
     - 체크박스 (`<en-todo>`)
     - 링크, 굵게, 기울임
     - 이미지 참조 (`<en-media hash="...">`)
     - 코드블록

3. Notion 블록 빌더
   - `block_builder.py`: Markdown → Notion block JSON
   - 블록 타입별 JSON 구조 생성
   - 2000자 제한 처리 (긴 텍스트 분할)

**체크포인트**:
- [ ] 샘플 노트의 ENML → Markdown 변환 성공
- [ ] Notion 블록 JSON 구조 생성 확인
- [ ] 체크박스, 리스트, 제목 등 특수 요소 변환 확인

---

### Phase 3: Notion API 연동 (2일)

**목표**: Notion에 페이지 생성 및 블록 추가

**작업**:
1. Notion API 설정
   - Notion Integration 생성 (https://www.notion.so/my-integrations)
   - Internal Integration Token 발급
   - 대상 페이지/데이터베이스에 Integration 권한 부여

2. Notion 클라이언트 개발
   - `notion/client.py`: API 래퍼 클래스
   - 인증, 에러 핸들링
   - `notion/page_creator.py`: 페이지 생성 로직
   - 속도 제한 처리 (`rate_limiter.py`)

3. 테스트 스크립트
   - `scripts/test_notion_api.py`: 연결 테스트
   - 샘플 페이지 생성 테스트

**체크포인트**:
- [ ] Notion API 인증 성공
- [ ] 테스트 페이지 생성 성공
- [ ] 블록 추가 (paragraph, heading) 성공

---

### Phase 4: 이미지 및 리소스 처리 (3-4일) ⚠️ 중요

**목표**: 1,574개 리소스 추출 및 업로드 (9가지 포맷 지원)

**작업**:
1. 리소스 추출 및 분류
   - `resources/resource_extractor.py`: Base64 디코딩, MD5 해시 생성
   - 임시 디렉토리 저장 (`data/temp/{note_id}/{hash}.{ext}`)
   - MIME 타입별 처리기 구현:
     - **이미지** (1,557개): `image_handler.py`
       - JPEG (1,383), PNG (160), SVG (13), WebP (1)
       - 크기 최적화 (Pillow) - 대용량 이미지 리사이즈
     - **문서** (13개): `document_handler.py`
       - PDF (11), DOCX (1), PPTX (1)
     - **텍스트** (4개): `text_handler.py`
       - Markdown (3), Plain Text (1)

2. 파일 업로드 전략 ⚠️ 핵심 결정 필요

   **옵션 A: AWS S3 + CloudFront (권장)**
   - 장점: 안정적, 빠름, 1,574개 대량 처리 가능
   - 비용: S3 스토리지 ($0.023/GB) + CloudFront ($0.085/GB 전송)
   - 예상 비용: 약 $1-2/월 (500MB 기준)
   - 구현: `boto3` 라이브러리 사용

   **옵션 B: Cloudinary (무료 티어)**
   - 장점: 무료 25 크레딧/월, 이미지 자동 최적화
   - 단점: 제한적 (25GB 대역폭), 이미지만 지원 (PDF/Office 불가)
   - 구현: `cloudinary` 라이브러리

   **옵션 C: Imgur API (무료)**
   - 장점: 무료, 간단
   - 단점: 일일 12,500 업로드 제한, 이미지만 (PDF 불가), 안정성 낮음
   - 구현: `imgurpython` 라이브러리

   **옵션 D: 로컬 HTTP 서버 (임시)**
   - 장점: 비용 없음
   - 단점: Notion이 fetch하는 동안만 서버 유지 필요, 공개 IP/ngrok 필요
   - 구현: `flask` 간단 서버 + `ngrok`

3. 리소스-본문 매칭
   - `<en-media hash="...">` 태그에서 해시 추출
   - MD5 해시로 리소스 객체 찾기
   - 업로드된 URL로 치환

4. Notion 블록 생성
   - `image` 블록: 외부 URL 사용
   - `file` 블록: PDF, Office 문서
   - `code` 블록: Markdown, Plain Text (인라인 표시)

5. 대량 업로드 최적화
   - 멀티스레딩 (ThreadPoolExecutor) - 10개 동시 업로드
   - 진행률 표시 (tqdm)
   - 실패 재시도 (3회)
   - 업로드 캐시 (이미 업로드된 리소스는 재사용)

**체크포인트**:
- [ ] 모든 MIME 타입 Base64 디코딩 성공
- [ ] 파일 업로드 전략 결정 및 구현
- [ ] 1,574개 리소스 중 95% 이상 업로드 성공
- [ ] MD5 해시 매칭 정확도 100%
- [ ] 블로그_예전모음.enex (1,192개 리소스) 처리 성공
- [ ] 업로드 실패 리소스 로그 및 fallback 처리

---

### Phase 5: 전체 마이그레이션 파이프라인 (2-3일)

**목표**: 26개 파일 일괄 처리 및 오류 처리

**작업**:
1. 메인 실행 스크립트
   - `main.py`: 전체 워크플로우 orchestration
   - 파일별 순차 처리
   - 진행률 표시 (tqdm)

2. 체크포인트 시스템
   - 처리 완료된 파일/노트 기록
   - 중단 시 재개 가능 (resume)
   - `data/checkpoint/migration_state.json`

3. 에러 핸들링
   - 네트워크 에러 재시도
   - API 속도 제한 대응
   - 파싱 실패 시 로깅 및 스킵
   - 실패한 노트 목록 별도 저장

4. 로깅
   - `utils/logger.py`: 구조화된 로그
   - 파일별 처리 시간, 노트 개수, 성공/실패 통계

**체크포인트**:
- [ ] 단일 .enex 파일 완전 마이그레이션 성공
- [ ] 체크포인트 저장/복원 기능 작동
- [ ] 26개 파일 전체 마이그레이션 성공

---

### Phase 6: 최적화 및 문서화 (1-2일)

**목표**: 성능 개선 및 사용자 문서 작성

**작업**:
1. 성능 최적화
   - 대용량 파일 스트리밍 파싱 (메모리 절약)
   - 병렬 처리 고려 (Notion API 속도 제한 내에서)
   - 이미지 크기 최적화

2. CLI 인터페이스 개선
   - argparse로 옵션 추가:
     - `--file <파일명>`: 특정 파일만 처리
     - `--resume`: 체크포인트부터 재개
     - `--dry-run`: 실제 업로드 없이 시뮬레이션
     - `--parent-page <page_id>`: 대상 Notion 페이지

3. 문서화
   - `README.md`: 설치, 설정, 사용법
   - `PROJECT_PLAN.md`: 이 문서 업데이트
   - 주석 및 docstring 추가

**체크포인트**:
- [ ] 대용량 파일 처리 시간 50% 단축
- [ ] README 작성 완료
- [ ] 모든 함수에 docstring 추가

---

## 기술적 도전과제 및 해결방안

### 1. 대량 리소스 업로드 (1,574개) ⚠️ 최대 난제
**문제**:
- Notion API는 Base64 직접 업로드 불가, 외부 URL만 허용
- 1,574개 파일을 어디에 호스팅할 것인가?
- 블로그_예전모음.enex 하나에만 1,192개 리소스

**해결방안**:
- **권장**: AWS S3 + CloudFront (비용 $1-2/월, 안정적)
- **무료 옵션**: Cloudinary (25GB/월 무료) + Imgur (이미지 백업)
- **임시**: ngrok + 로컬 HTTP 서버 (테스트용)
- **멀티스레딩**: 10개 동시 업로드로 속도 향상
- **재시도 로직**: 실패 시 3회 재시도, 그래도 실패하면 로그

### 2. 다양한 파일 포맷 (9가지)
**문제**: JPEG, PNG, SVG, WebP, PDF, DOCX, PPTX, Markdown, Plain Text

**해결방안**:
- 포맷별 핸들러 구현
- SVG: 이미지 블록 (Notion이 자체 렌더링)
- WebP: PNG로 변환 (Pillow)
- PDF/Office: `file` 블록 (외부 URL)
- Markdown/Text: `code` 블록 또는 인라인 텍스트

### 3. API 속도 제한 vs 대량 데이터
**문제**:
- Notion API 초당 3회 제한
- 1,373개 노트 + 1,574개 리소스 = 수천 개 API 호출
- 예상 처리 시간: 최소 8-10시간

**해결방안**:
- `rate_limiter.py`: 요청 간 0.35초 지연
- 지수 백오프 재시도 (429 Too Many Requests)
- 배치 블록 추가 (한 번에 100개 블록)
- 체크포인트 시스템 (중단 시 재개)
- 야간 실행 권장

### 4. 대용량 XML 파싱
**문제**: 160MB XML 파일은 메모리 부담

**해결방안**:
- `lxml.etree.iterparse()` 사용 (스트리밍)
- 노트 단위로 순차 처리
- 리소스는 on-demand 로딩

### 5. ENML 특수 요소
**문제**: Evernote만의 특수 태그 (`<en-todo>`, `<en-media>`, `<en-crypt>` 등)

**해결방안**:
- `<en-todo>`: Notion `to_do` 블록
- `<en-media>`: MD5 해시로 리소스 매칭
- `<en-crypt>`: 암호화된 영역은 경고 후 스킵
- HTML 유사 태그: BeautifulSoup로 파싱

### 6. MD5 해시 매칭 복잡도
**문제**:
- ENML: `<en-media hash="34c08f...">`
- 리소스: Base64 디코딩 → MD5 해시
- O(n×m) 복잡도 (노트 × 리소스)

**해결방안**:
- 리소스 해시 딕셔너리 사전 구축 O(1) 조회
- 노트별 리소스 그룹화

### 7. 한글 인코딩 문제
**문제**: XML 파싱 시 한글 깨짐 가능성

**해결방안**:
- `encoding='UTF-8'` 명시
- `lxml` 사용 (robust)

---

## 데이터 모델

### ENEX 노트 구조 (파싱 후)
```python
@dataclass
class EvernoteNote:
    title: str
    content: str  # ENML
    created: datetime
    updated: datetime
    tags: List[str]
    author: Optional[str]
    source_url: Optional[str]
    resources: List[Resource]  # 이미지, 첨부파일

@dataclass
class Resource:
    data: bytes  # Base64 디코딩 후
    mime: str  # 9가지 타입 지원
    filename: Optional[str]
    width: Optional[int]
    height: Optional[int]
    hash: str  # MD5 해시 (ENML 매칭용)
    source_url: Optional[str]  # 원본 URL (있는 경우)
    uploaded_url: Optional[str]  # 업로드 후 URL (S3/Cloudinary)

    def get_extension(self) -> str:
        """MIME 타입에서 파일 확장자 추출"""
        mime_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'image/svg+xml': 'svg',
            'image/webp': 'webp',
            'application/pdf': 'pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
            'text/markdown': 'md',
            'text/plain': 'txt',
        }
        return mime_map.get(self.mime, 'bin')
```

### Notion 페이지 구조
```python
@dataclass
class NotionPage:
    title: str
    parent_id: str  # 부모 페이지 또는 데이터베이스 ID
    properties: Dict[str, Any]  # 태그, 날짜 등
    children: List[Block]  # 블록 목록

@dataclass
class Block:
    type: str  # "paragraph", "heading_1", "image", etc.
    content: Dict[str, Any]  # 블록별 content 구조
```

---

## 테스트 계획

### 단위 테스트
- `tests/test_parser.py`: ENEX 파싱 로직
- `tests/test_converter.py`: ENML → Markdown 변환
- `tests/test_notion_client.py`: Notion API 호출 (mock)

### 통합 테스트
- 작은 샘플 파일로 end-to-end 테스트
- 이미지 포함 노트 처리 확인

### 수동 테스트
- 각 .enex 파일별로 샘플 노트 1개씩 수동 확인
- Notion에서 렌더링 결과 검증

---

## 예상 일정

| Phase | 작업 내용 | 예상 기간 | 비고 |
|-------|----------|---------|------|
| Phase 1 | 환경 설정 및 ENEX 파싱 | 1-2일 | 1,373개 노트 파싱 |
| Phase 2 | ENML → Notion 변환 | 2-3일 | ENML 태그 처리 |
| Phase 3 | Notion API 연동 | 2일 | 기본 페이지 생성 |
| Phase 4 | **리소스 처리** | **3-4일** | **1,574개 파일 업로드** |
| Phase 5 | 전체 파이프라인 | 2-3일 | end-to-end 통합 |
| Phase 6 | 최적화 및 문서화 | 1-2일 | 성능 튜닝 |
| **합계** | | **11-16일** | **실행 시간 8-10시간** |

**참고**: 실제 마이그레이션 실행 시간은 8-10시간 소요 예상 (Notion API 속도 제한)

---

## 리스크 및 대응

### 높은 리스크
1. **1,574개 리소스 업로드 실패** ⚠️
   - 규모: 블로그_예전모음.enex 하나에만 1,192개
   - 대응: AWS S3 또는 Cloudinary 선택 (Phase 4 초반 결정)
   - 대응: 업로드 실패 시 fallback 전략 (URL만 기록)

2. **API 속도 제한 (8-10시간 처리 시간)**
   - 규모: 1,373 노트 + 1,574 리소스 = 수천 건 API 호출
   - 대응: 체크포인트 시스템 (중단/재개)
   - 대응: 야간 실행 권장

3. **다양한 파일 포맷 (9가지) 처리 복잡도**
   - 대응: 점진적 지원 (이미지 우선 → 문서 → 텍스트)
   - 대응: 미지원 포맷은 경고 후 fallback

### 중간 리스크
1. **대용량 XML 파싱 (160MB)**
   - 대응: 스트리밍 파싱 + 메모리 모니터링

2. **ENML 특수 요소 복잡도**
   - 대응: 핵심 요소 우선 (<en-media>, <en-todo>)
   - 대응: 나머지는 일반 텍스트 fallback

3. **한글 인코딩 문제**
   - 대응: UTF-8 명시 + lxml 사용

---

## 향후 확장 가능성

1. **GUI 인터페이스**: Tkinter 또는 웹 기반 UI
2. **양방향 동기화**: Notion → Evernote 역변환
3. **다른 노트앱 지원**: OneNote, Bear, Apple Notes 등
4. **데이터베이스 마이그레이션**: Notion 데이터베이스로 구조화
5. **태그 기반 자동 분류**: 태그별로 Notion 페이지 계층 구조 생성

---

## 참고 자료

### Evernote
- [ENEX DTD](http://xml.evernote.com/pub/evernote-export3.dtd)
- [ENML Specification](http://dev.evernote.com/doc/articles/enml.php)

### Notion
- [Notion API Documentation](https://developers.notion.com/)
- [Python SDK](https://github.com/ramnes/notion-sdk-py)
- [Block Types](https://developers.notion.com/reference/block)

### 유사 프로젝트
- [evernote2md](https://github.com/wormi4ok/evernote2md) (Go)
- [notion-py](https://github.com/jamalex/notion-py) (비공식 API)

---

## 개발자 노트

### 우선순위
1. 텍스트 콘텐츠 마이그레이션 (가장 중요)
2. 메타데이터 보존 (제목, 날짜, 태그)
3. 이미지 마이그레이션
4. 특수 요소 (체크박스, 코드블록)

### 품질 목표
- **노트 성공률**: 95% 이상 (1,373개 중 1,300개 이상)
- **리소스 성공률**: 90% 이상 (1,574개 중 1,415개 이상)
- **데이터 손실**: 0% 텍스트 보존 (최소 목표)
- **성능**: 노트당 평균 5초 이내 처리 (리소스 제외)

---

## 부록: 실제 데이터 분석 결과

### 전체 통계
```
총 ENEX 파일: 23개
총 노트: 1,373개
총 리소스: 1,574개
총 용량: ~450MB

리소스 분포:
- 리소스 있는 파일: 17개 (73.9%)
- 리소스 없는 파일: 6개 (26.1%)
```

### 파일별 상세 현황
```
블로그_예전모음.enex    : 60 노트, 1,192 리소스 (160MB) ⚠️ 최대 난제
책정리.enex             : 413 노트, 87 리소스 (116MB)
첫 번째 노트북.enex     : 204 노트, 49 리소스 (13.7MB)
블랙야크.enex           : 103 노트, 68 리소스 (29MB)
일상이야기.enex         : 92 노트, 16 리소스 (19.2MB)
미국출장이야기.enex     : 80 노트, 25 리소스 (31MB)
그냥 이야기.enex        : 73 노트, 22 리소스 (7.6MB)
ETF 바이브 코딩.enex    : 64 노트, 32 리소스 (5.9MB)
주간일기.enex           : 64 노트, 1 리소스 (0.6MB)
IT트렌드.enex           : 45 노트, 21 리소스 (4.2MB)
책 작성.enex            : 44 노트, 33 리소스 (56.9MB)
직장이야기.enex         : 29 노트, 4 리소스 (2.6MB)
투자생각정리.enex       : 26 노트, 13 리소스 (4.1MB)
책초안_2505.enex        : 14 노트, 7 리소스 (0.9MB)
부동산분석('25.06).enex : 8 노트, 1 리소스 (1.4MB)
냅킨경제학.enex         : 3 노트, 2 리소스 (0.9MB)
돌봄학개론.enex         : 3 노트, 1 리소스 (3.5MB)
```

### 리소스 포맷 상세
| MIME Type | 개수 | 비율 | 처리 방법 |
|-----------|------|------|-----------|
| image/jpeg | 1,383 | 87.9% | Notion image 블록 |
| image/png | 160 | 10.2% | Notion image 블록 |
| image/svg+xml | 13 | 0.8% | Notion image 블록 |
| application/pdf | 11 | 0.7% | Notion file/pdf 블록 |
| text/markdown | 3 | 0.2% | Notion code 블록 |
| image/webp | 1 | 0.1% | PNG 변환 후 image 블록 |
| application/vnd.openxmlformats-officedocument.wordprocessingml.document | 1 | 0.1% | Notion file 블록 |
| application/vnd.openxmlformats-officedocument.presentationml.presentation | 1 | 0.1% | Notion file 블록 |
| text/plain | 1 | 0.1% | Notion code 블록 |
| **합계** | **1,574** | **100%** | |

### 핵심 발견
1. **이미지 중심**: 전체 리소스의 98.9% (1,557개)가 이미지
2. **문서 파일 소량**: PDF 11개, Office 2개만 존재
3. **극단적 분포**: 블로그_예전모음.enex 하나가 전체 리소스의 75.7% 차지
4. **리소스 매칭 필수**: 모든 리소스는 ENML에서 MD5 해시로 참조됨
5. **파일명 보존**: 1,574개 모두 filename 속성 존재 (보존 가능)

---

**작성일**: 2025-10-25
**버전**: 2.0 (실제 데이터 분석 반영)
**작성자**: Claude Code
**마지막 업데이트**: 2025-10-25 (ENEX 파일 실제 분석 완료)
