# Evernote to Notion Migration - 상세 Task 목록

**프로젝트**: 에버노트 → 노션 마이그레이션 도구
**데이터 규모**: 23개 파일, 1,373개 노트, 1,574개 리소스
**예상 기간**: 11-16일

---

## Phase 1: 환경 설정 및 ENEX 파싱 (1-2일)

### Task 1.1: 프로젝트 초기화 (2시간)
- [ ] 1.1.1 디렉토리 구조 생성
  ```bash
  mkdir -p app/{parsers,notion,resources,utils}
  mkdir -p scripts data/{temp,logs,checkpoint} tests
  touch app/__init__.py
  touch app/parsers/__init__.py app/notion/__init__.py
  touch app/resources/__init__.py app/utils/__init__.py
  ```
- [ ] 1.1.2 Git 저장소 초기화
  ```bash
  git init
  echo "venv/" > .gitignore
  echo ".env" >> .gitignore
  echo "data/temp/*" >> .gitignore
  echo "__pycache__/" >> .gitignore
  echo "*.pyc" >> .gitignore
  ```
- [ ] 1.1.3 `requirements.txt` 작성
  ```
  # Notion API
  notion-client==2.2.1

  # XML 파싱
  lxml==5.1.0
  beautifulsoup4==4.12.3

  # 이미지 처리
  Pillow==10.2.0

  # 파일 업로드 (선택적)
  boto3==1.34.51  # AWS S3
  cloudinary==1.39.0  # Cloudinary

  # 유틸리티
  python-dotenv==1.0.1
  tqdm==4.66.2
  requests==2.31.0

  # 테스트
  pytest==8.0.1
  pytest-cov==4.1.0
  ```
- [ ] 1.1.4 `.env.example` 작성
  ```
  # Notion API
  NOTION_API_KEY=secret_xxxxxxxxxxxxxxxxxxxxx
  NOTION_PARENT_PAGE_ID=xxxxxxxxxxxxxxxxxxxxx

  # 파일 업로드 전략 (s3 | cloudinary | imgur | local)
  UPLOAD_STRATEGY=s3

  # AWS S3 (UPLOAD_STRATEGY=s3인 경우)
  AWS_ACCESS_KEY_ID=
  AWS_SECRET_ACCESS_KEY=
  AWS_S3_BUCKET=evernote-migration
  AWS_REGION=ap-northeast-2

  # Cloudinary (UPLOAD_STRATEGY=cloudinary인 경우)
  CLOUDINARY_CLOUD_NAME=
  CLOUDINARY_API_KEY=
  CLOUDINARY_API_SECRET=

  # Imgur (UPLOAD_STRATEGY=imgur인 경우)
  IMGUR_CLIENT_ID=

  # 소스 디렉토리
  ENEX_SOURCE_DIR=/Users/sunchulkim/evernote

  # 로깅
  LOG_LEVEL=INFO
  ```
- [ ] 1.1.5 가상환경 생성 및 의존성 설치
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

**완료 기준**: 디렉토리 구조 생성, Git 초기화, 의존성 설치 완료

---

### Task 1.2: 기본 ENEX 파서 개발 (4-6시간)

#### 1.2.1 ENEX 파서 클래스 구현
- [ ] `app/parsers/enex_parser.py` 생성
- [ ] `EnexParser` 클래스 구현
  - [ ] `__init__(file_path)`: 파일 경로 초기화
  - [ ] `parse() -> List[EvernoteNote]`: 전체 노트 파싱
  - [ ] `_parse_note(note_element) -> EvernoteNote`: 단일 노트 파싱
  - [ ] `_parse_resources(note_element) -> List[Resource]`: 리소스 추출
  - [ ] `_calculate_md5(data: bytes) -> str`: MD5 해시 계산
- [ ] 스트리밍 파싱 구현 (`lxml.etree.iterparse`)
  ```python
  def parse(self) -> Generator[EvernoteNote, None, None]:
      context = ET.iterparse(self.file_path, events=('start', 'end'))
      for event, elem in context:
          if event == 'end' and elem.tag == 'note':
              yield self._parse_note(elem)
              elem.clear()  # 메모리 절약
  ```

#### 1.2.2 데이터 모델 정의
- [ ] `app/models.py` 생성
- [ ] `EvernoteNote` 데이터클래스
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
      resources: List[Resource]
  ```
- [ ] `Resource` 데이터클래스
  ```python
  @dataclass
  class Resource:
      data: bytes
      mime: str
      filename: Optional[str]
      width: Optional[int]
      height: Optional[int]
      hash: str  # MD5
      source_url: Optional[str]
      uploaded_url: Optional[str] = None

      def get_extension(self) -> str:
          # MIME → 확장자 매핑
  ```

#### 1.2.3 날짜/시간 파싱
- [ ] `_parse_datetime(date_str: str) -> datetime` 구현
  - 형식: `20200101T120000Z` (ISO 8601)
  ```python
  from datetime import datetime
  def _parse_datetime(date_str: str) -> datetime:
      return datetime.strptime(date_str, '%Y%m%dT%H%M%SZ')
  ```

**완료 기준**:
- 맛집.enex (3 노트, 0 리소스) 파싱 성공
- 냅킨경제학.enex (3 노트, 2 리소스) 파싱 성공
- 모든 필드 정상 추출 확인

---

### Task 1.3: 파싱 테스트 스크립트 작성 (2-3시간)

- [ ] 1.3.1 `scripts/test_enex_parse.py` 작성
  ```python
  import sys
  from pathlib import Path
  from app.parsers.enex_parser import EnexParser

  def test_single_file(file_path):
      parser = EnexParser(file_path)
      notes = list(parser.parse())

      print(f"File: {Path(file_path).name}")
      print(f"Notes: {len(notes)}")

      for i, note in enumerate(notes[:3]):  # 첫 3개만
          print(f"\nNote {i+1}:")
          print(f"  Title: {note.title}")
          print(f"  Created: {note.created}")
          print(f"  Tags: {note.tags}")
          print(f"  Resources: {len(note.resources)}")

          for j, res in enumerate(note.resources[:2]):
              print(f"    Resource {j+1}:")
              print(f"      MIME: {res.mime}")
              print(f"      Hash: {res.hash}")
              print(f"      Filename: {res.filename}")
  ```

- [ ] 1.3.2 전체 파일 통계 스크립트 작성
  ```python
  def analyze_all_files(source_dir):
      total_notes = 0
      total_resources = 0

      for enex_file in Path(source_dir).glob("*.enex"):
          parser = EnexParser(str(enex_file))
          notes = list(parser.parse())

          note_count = len(notes)
          resource_count = sum(len(n.resources) for n in notes)

          total_notes += note_count
          total_resources += resource_count

          print(f"{enex_file.name:40s} | {note_count:4d} notes | {resource_count:4d} resources")

      print(f"\nTotal: {total_notes} notes, {total_resources} resources")
  ```

- [ ] 1.3.3 Tier별 테스트 실행
  - Tier 1: 맛집.enex (리소스 없음)
  - Tier 2: 냅킨경제학.enex, 돌봄학개론.enex (리소스 소량)
  - Tier 3: IT트렌드.enex (21 리소스, 9가지 포맷 포함)

**완료 기준**:
- 23개 파일 모두 파싱 에러 없음
- 총 1,373 노트, 1,574 리소스 확인
- MIME 타입 9가지 모두 감지

---

### Task 1.4: 대용량 파일 처리 검증 (1-2시간)

- [ ] 1.4.1 블로그_예전모음.enex (160MB) 파싱 테스트
  - 메모리 사용량 모니터링
  - 파싱 시간 측정
- [ ] 1.4.2 책정리.enex (116MB) 파싱 테스트
- [ ] 1.4.3 메모리 프로파일링
  ```python
  import tracemalloc

  tracemalloc.start()
  parser = EnexParser("블로그_예전모음.enex")
  notes = list(parser.parse())
  current, peak = tracemalloc.get_traced_memory()
  print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
  ```

**완료 기준**: 160MB 파일을 500MB 이하 메모리로 파싱 성공

---

## Phase 2: ENML → Notion 블록 변환 (2-3일)

### Task 2.1: ENML 분석 및 샘플 수집 (3-4시간)

- [ ] 2.1.1 ENML 태그 목록 추출
  ```python
  import re
  from collections import Counter

  def extract_enml_tags(enex_file):
      parser = EnexParser(enex_file)
      tag_counter = Counter()

      for note in parser.parse():
          tags = re.findall(r'<(\w+)', note.content)
          tag_counter.update(tags)

      return tag_counter
  ```
- [ ] 2.1.2 태그별 샘플 ENML 저장
  - `<div>`, `<span>`, `<br>`
  - `<h1>`, `<h2>`, `<h3>`
  - `<ul>`, `<ol>`, `<li>`
  - `<en-todo>` (체크박스)
  - `<en-media>` (이미지/파일 참조)
  - `<a>`, `<b>`, `<i>`, `<u>`
  - `<table>`, `<tr>`, `<td>`

- [ ] 2.1.3 특수 케이스 수집
  - HTML 엔티티 (`&nbsp;`, `&lt;`, `&gt;`)
  - 중첩 태그
  - 스타일 속성 (`style="color:rgb(0,0,0)"`)

**완료 기준**: 최소 20가지 ENML 패턴 수집

---

### Task 2.2: ENML → Markdown 변환기 개발 (6-8시간)

#### 2.2.1 기본 변환기 구현
- [ ] `app/parsers/enml_converter.py` 생성
- [ ] `EnmlConverter` 클래스
  ```python
  class EnmlConverter:
      def __init__(self, resource_hash_map: Dict[str, Resource]):
          self.resources = resource_hash_map

      def convert(self, enml: str) -> List[NotionBlock]:
          # CDATA 제거
          enml = self._extract_from_cdata(enml)

          # BeautifulSoup 파싱
          soup = BeautifulSoup(enml, 'lxml')

          # 블록 변환
          blocks = []
          for element in soup.find('en-note').children:
              block = self._convert_element(element)
              if block:
                  blocks.append(block)

          return blocks
  ```

#### 2.2.2 요소별 변환 로직
- [ ] `_convert_heading(element)` - h1~h6 → heading_1~3
- [ ] `_convert_paragraph(element)` - div/p → paragraph
- [ ] `_convert_list(element)` - ul/ol → bulleted_list/numbered_list
- [ ] `_convert_todo(element)` - en-todo → to_do
- [ ] `_convert_media(element)` - en-media → image/file
  ```python
  def _convert_media(self, element):
      hash_value = element.get('hash')
      mime_type = element.get('type')

      resource = self.resources.get(hash_value)
      if not resource:
          return None  # 리소스 못 찾음

      if mime_type.startswith('image/'):
          return {
              'type': 'image',
              'image': {
                  'type': 'external',
                  'external': {'url': resource.uploaded_url}
              }
          }
      else:
          return {
              'type': 'file',
              'file': {
                  'type': 'external',
                  'external': {'url': resource.uploaded_url}
              }
          }
  ```

#### 2.2.3 Rich Text 변환
- [ ] 굵게 (`<b>`, `<strong>`) → `bold: true`
- [ ] 기울임 (`<i>`, `<em>`) → `italic: true`
- [ ] 밑줄 (`<u>`) → `underline: true`
- [ ] 링크 (`<a href="...">`) → `link: {url: "..."}`
- [ ] 코드 (`<code>`) → `code: true`

#### 2.2.4 HTML 엔티티 디코딩
- [ ] `&nbsp;` → 공백
- [ ] `&lt;` → `<`
- [ ] `&gt;` → `>`
- [ ] `&amp;` → `&`

**완료 기준**:
- 샘플 ENML 20가지 모두 변환 성공
- Rich Text 포맷 유지
- 이미지 참조 (hash) 정상 매핑

---

### Task 2.3: Notion 블록 빌더 개발 (4-6시간)

- [ ] 2.3.1 `app/notion/block_builder.py` 생성
- [ ] 2.3.2 블록 타입별 JSON 생성
  ```python
  class BlockBuilder:
      @staticmethod
      def paragraph(text: str, annotations: dict = None) -> dict:
          return {
              'type': 'paragraph',
              'paragraph': {
                  'rich_text': [BlockBuilder._rich_text(text, annotations)]
              }
          }

      @staticmethod
      def heading_1(text: str) -> dict:
          return {
              'type': 'heading_1',
              'heading_1': {
                  'rich_text': [BlockBuilder._rich_text(text)]
              }
          }

      @staticmethod
      def image(url: str, caption: str = None) -> dict:
          block = {
              'type': 'image',
              'image': {
                  'type': 'external',
                  'external': {'url': url}
              }
          }
          if caption:
              block['image']['caption'] = [BlockBuilder._rich_text(caption)]
          return block

      @staticmethod
      def to_do(text: str, checked: bool = False) -> dict:
          return {
              'type': 'to_do',
              'to_do': {
                  'rich_text': [BlockBuilder._rich_text(text)],
                  'checked': checked
              }
          }
  ```

- [ ] 2.3.3 2000자 제한 처리
  ```python
  def split_long_text(text: str, max_length: int = 2000) -> List[str]:
      """긴 텍스트를 2000자 단위로 분할"""
      chunks = []
      while len(text) > max_length:
          # 단어 경계에서 분할
          split_pos = text.rfind(' ', 0, max_length)
          if split_pos == -1:
              split_pos = max_length
          chunks.append(text[:split_pos])
          text = text[split_pos:].lstrip()
      chunks.append(text)
      return chunks
  ```

**완료 기준**: 모든 블록 타입 JSON 생성 함수 구현

---

### Task 2.4: 변환 테스트 (2-3시간)

- [ ] 2.4.1 단위 테스트 작성 (`tests/test_converter.py`)
  ```python
  def test_heading_conversion():
      enml = '<en-note><h1>제목</h1></en-note>'
      converter = EnmlConverter({})
      blocks = converter.convert(enml)

      assert blocks[0]['type'] == 'heading_1'
      assert blocks[0]['heading_1']['rich_text'][0]['text']['content'] == '제목'
  ```

- [ ] 2.4.2 실제 노트 변환 테스트
  - 맛집.enex 첫 번째 노트 변환
  - IT트렌드.enex 첫 번째 노트 변환 (이미지 포함)

- [ ] 2.4.3 Edge Case 테스트
  - 빈 노트
  - 이미지만 있는 노트
  - 매우 긴 텍스트 (2000자 이상)

**완료 기준**: pytest 통과율 100%

---

## Phase 3: Notion API 연동 (2일)

### Task 3.1: Notion Integration 설정 (1시간)

- [ ] 3.1.1 Notion Integration 생성
  - https://www.notion.so/my-integrations 방문
  - "New integration" 클릭
  - 이름: "Evernote Migration"
  - Capabilities: Read/Write content
  - Internal Integration Token 복사

- [ ] 3.1.2 대상 페이지에 Integration 권한 부여
  - Notion 페이지 열기 (마이그레이션 대상)
  - `...` 메뉴 → "Connections" → "Evernote Migration" 선택
  - 페이지 ID 복사 (URL에서 추출)

- [ ] 3.1.3 `.env` 파일 생성
  ```bash
  cp .env.example .env
  # NOTION_API_KEY, NOTION_PARENT_PAGE_ID 입력
  ```

**완료 기준**: `.env` 설정 완료, 페이지 ID 확인

---

### Task 3.2: Notion API 클라이언트 개발 (4-6시간)

#### 3.2.1 기본 클라이언트 구현
- [ ] `app/notion/client.py` 생성
  ```python
  from notion_client import Client
  from typing import List, Dict, Any

  class NotionClient:
      def __init__(self, api_key: str):
          self.client = Client(auth=api_key)

      def create_page(self, parent_id: str, title: str,
                      properties: dict = None) -> str:
          """페이지 생성, 페이지 ID 반환"""
          page = self.client.pages.create(
              parent={'page_id': parent_id},
              properties={
                  'title': {
                      'title': [{'text': {'content': title}}]
                  },
                  **(properties or {})
              }
          )
          return page['id']

      def append_blocks(self, page_id: str, blocks: List[dict]) -> None:
          """블록 추가 (최대 100개씩 배치)"""
          # 100개씩 분할
          for i in range(0, len(blocks), 100):
              batch = blocks[i:i+100]
              self.client.blocks.children.append(
                  block_id=page_id,
                  children=batch
              )
  ```

#### 3.2.2 에러 핸들링
- [ ] Rate Limit 처리 (429 Too Many Requests)
  ```python
  import time
  from notion_client.errors import APIResponseError

  def _request_with_retry(self, func, *args, max_retries=3, **kwargs):
      for attempt in range(max_retries):
          try:
              return func(*args, **kwargs)
          except APIResponseError as e:
              if e.code == 'rate_limited':
                  wait_time = 2 ** attempt  # 지수 백오프
                  time.sleep(wait_time)
              else:
                  raise
      raise Exception("Max retries exceeded")
  ```

#### 3.2.3 Rate Limiter 구현
- [ ] `app/utils/rate_limiter.py` 생성
  ```python
  import time
  from threading import Lock

  class RateLimiter:
      def __init__(self, calls_per_second: int = 3):
          self.min_interval = 1.0 / calls_per_second
          self.last_call = 0
          self.lock = Lock()

      def wait(self):
          with self.lock:
              now = time.time()
              elapsed = now - self.last_call
              if elapsed < self.min_interval:
                  time.sleep(self.min_interval - elapsed)
              self.last_call = time.time()
  ```

**완료 기준**: API 호출 성공, Rate Limit 회피

---

### Task 3.3: 페이지 생성기 개발 (3-4시간)

- [ ] 3.3.1 `app/notion/page_creator.py` 생성
  ```python
  class PageCreator:
      def __init__(self, client: NotionClient, parent_id: str):
          self.client = client
          self.parent_id = parent_id

      def create_from_note(self, note: EvernoteNote) -> str:
          # 페이지 속성 구성
          properties = self._build_properties(note)

          # 페이지 생성
          page_id = self.client.create_page(
              parent_id=self.parent_id,
              title=note.title,
              properties=properties
          )

          # 블록 변환
          converter = EnmlConverter(self._build_resource_map(note))
          blocks = converter.convert(note.content)

          # 블록 추가
          self.client.append_blocks(page_id, blocks)

          return page_id

      def _build_properties(self, note: EvernoteNote) -> dict:
          """Notion 페이지 속성 구성"""
          props = {}

          # 태그 (Multi-select)
          if note.tags:
              props['Tags'] = {
                  'multi_select': [{'name': tag} for tag in note.tags]
              }

          # 생성일 (Date)
          props['Created'] = {
              'date': {'start': note.created.isoformat()}
          }

          # 수정일
          props['Updated'] = {
              'date': {'start': note.updated.isoformat()}
          }

          return props
  ```

- [ ] 3.3.2 메타데이터 보존
  - 태그 → Multi-select 속성
  - 생성일 → Date 속성
  - 수정일 → Date 속성
  - 작성자 → Text 속성 (선택)
  - 원본 URL → URL 속성 (선택)

**완료 기준**: 테스트 페이지 생성 성공 (메타데이터 포함)

---

### Task 3.4: API 연동 테스트 (2-3시간)

- [ ] 3.4.1 `scripts/test_notion_api.py` 작성
  ```python
  def test_create_simple_page():
      client = NotionClient(os.getenv('NOTION_API_KEY'))
      parent_id = os.getenv('NOTION_PARENT_PAGE_ID')

      # 간단한 페이지 생성
      page_id = client.create_page(
          parent_id=parent_id,
          title="테스트 페이지"
      )
      print(f"Created page: {page_id}")

      # 블록 추가
      blocks = [
          BlockBuilder.heading_1("제목"),
          BlockBuilder.paragraph("본문 텍스트"),
          BlockBuilder.to_do("할 일", checked=False)
      ]
      client.append_blocks(page_id, blocks)
      print("Blocks added successfully")
  ```

- [ ] 3.4.2 실제 노트로 테스트
  - 맛집.enex 첫 번째 노트 → Notion 페이지 생성
  - 결과 확인 (Notion 웹에서)
  - 제목, 본문, 메타데이터 확인

- [ ] 3.4.3 속도 제한 테스트
  - 연속 10개 페이지 생성
  - Rate Limiter 동작 확인
  - 429 에러 없는지 확인

**완료 기준**:
- 테스트 페이지 생성 성공
- Rate Limiter 정상 작동
- 메타데이터 보존 확인

---

## Phase 4: 리소스 처리 (3-4일) ⚠️ 최대 난제

### Task 4.1: 리소스 추출 및 분류 (4-6시간)

#### 4.1.1 리소스 추출기 구현
- [ ] `app/resources/resource_extractor.py` 생성
  ```python
  class ResourceExtractor:
      def __init__(self, output_dir: str = "data/temp"):
          self.output_dir = Path(output_dir)

      def extract_resources(self, note: EvernoteNote) -> Dict[str, Resource]:
          """리소스 추출 및 로컬 저장"""
          resource_map = {}

          note_dir = self.output_dir / note.title[:50]  # 제목으로 디렉토리
          note_dir.mkdir(parents=True, exist_ok=True)

          for resource in note.resources:
              # 파일 저장
              ext = resource.get_extension()
              filename = f"{resource.hash}.{ext}"
              filepath = note_dir / filename

              with open(filepath, 'wb') as f:
                  f.write(resource.data)

              resource.local_path = str(filepath)
              resource_map[resource.hash] = resource

          return resource_map
  ```

#### 4.1.2 MIME 타입별 핸들러
- [ ] `app/resources/image_handler.py` - 이미지 처리
  ```python
  from PIL import Image

  class ImageHandler:
      @staticmethod
      def optimize(image_path: str, max_size: int = 2000) -> str:
          """이미지 크기 최적화"""
          img = Image.open(image_path)

          # 큰 이미지 리사이즈
          if max(img.size) > max_size:
              img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
              img.save(image_path, optimize=True, quality=85)

          return image_path

      @staticmethod
      def convert_webp_to_png(webp_path: str) -> str:
          """WebP → PNG 변환"""
          img = Image.open(webp_path)
          png_path = webp_path.replace('.webp', '.png')
          img.save(png_path, 'PNG')
          return png_path
  ```

- [ ] `app/resources/document_handler.py` - PDF/Office 문서
  ```python
  class DocumentHandler:
      @staticmethod
      def validate_pdf(pdf_path: str) -> bool:
          """PDF 유효성 검증"""
          try:
              with open(pdf_path, 'rb') as f:
                  header = f.read(4)
                  return header == b'%PDF'
          except:
              return False
  ```

**완료 기준**: 1,574개 리소스 모두 로컬 저장 성공

---

### Task 4.2: 파일 업로드 전략 결정 및 구현 (1일) ⚠️ 핵심 결정

#### 4.2.1 업로드 전략 선택
- [ ] **옵션 검토 및 결정**
  - [ ] AWS S3 검토 (비용: $1-2/월)
  - [ ] Cloudinary 검토 (무료: 25GB/월)
  - [ ] Imgur 검토 (무료, 이미지만)
  - [ ] 최종 결정 및 문서화

#### 4.2.2 AWS S3 구현 (선택 시)
- [ ] `app/resources/s3_uploader.py` 생성
  ```python
  import boto3
  from botocore.exceptions import ClientError

  class S3Uploader:
      def __init__(self):
          self.s3 = boto3.client(
              's3',
              aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
              aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
              region_name=os.getenv('AWS_REGION')
          )
          self.bucket = os.getenv('AWS_S3_BUCKET')

      def upload(self, file_path: str, resource: Resource) -> str:
          """파일 업로드, URL 반환"""
          key = f"evernote/{resource.hash}.{resource.get_extension()}"

          # Content-Type 설정
          extra_args = {'ContentType': resource.mime}

          # 업로드
          self.s3.upload_file(
              file_path,
              self.bucket,
              key,
              ExtraArgs=extra_args
          )

          # Public URL 생성
          url = f"https://{self.bucket}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{key}"
          return url
  ```

- [ ] S3 버킷 생성 및 설정
  ```bash
  # AWS CLI로 버킷 생성
  aws s3 mb s3://evernote-migration --region ap-northeast-2

  # Public 읽기 권한 설정
  aws s3api put-bucket-policy --bucket evernote-migration --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "PublicRead",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::evernote-migration/*"
    }]
  }'
  ```

#### 4.2.3 Cloudinary 구현 (선택 시)
- [ ] `app/resources/cloudinary_uploader.py` 생성
  ```python
  import cloudinary
  import cloudinary.uploader

  class CloudinaryUploader:
      def __init__(self):
          cloudinary.config(
              cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
              api_key=os.getenv('CLOUDINARY_API_KEY'),
              api_secret=os.getenv('CLOUDINARY_API_SECRET')
          )

      def upload(self, file_path: str, resource: Resource) -> str:
          """이미지 업로드"""
          result = cloudinary.uploader.upload(
              file_path,
              public_id=resource.hash,
              resource_type='auto'
          )
          return result['secure_url']
  ```

#### 4.2.4 Uploader Factory
- [ ] `app/resources/uploader.py` - 전략 패턴
  ```python
  class UploaderFactory:
      @staticmethod
      def create(strategy: str):
          if strategy == 's3':
              return S3Uploader()
          elif strategy == 'cloudinary':
              return CloudinaryUploader()
          elif strategy == 'imgur':
              return ImgurUploader()
          else:
              raise ValueError(f"Unknown strategy: {strategy}")
  ```

**완료 기준**:
- 업로드 전략 선택 완료
- 테스트 파일 10개 업로드 성공
- Public URL 정상 접근 확인

---

### Task 4.3: 대량 업로드 구현 (6-8시간) ✅ COMPLETED

#### 4.3.1 멀티스레드 업로더
- [x] `app/resources/batch_uploader.py` 생성
  ```python
  from concurrent.futures import ThreadPoolExecutor, as_completed
  from tqdm import tqdm

  class BatchUploader:
      def __init__(self, uploader, max_workers: int = 10):
          self.uploader = uploader
          self.max_workers = max_workers

      def upload_resources(self, resources: List[Resource]) -> Dict[str, str]:
          """병렬 업로드, {hash: url} 반환"""
          results = {}
          failed = []

          with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
              # 업로드 작업 제출
              future_to_resource = {
                  executor.submit(self._upload_single, res): res
                  for res in resources
              }

              # 진행률 표시
              with tqdm(total=len(resources), desc="Uploading") as pbar:
                  for future in as_completed(future_to_resource):
                      resource = future_to_resource[future]
                      try:
                          url = future.result()
                          results[resource.hash] = url
                          resource.uploaded_url = url
                      except Exception as e:
                          failed.append((resource, str(e)))
                      pbar.update(1)

          # 실패 로깅
          if failed:
              self._log_failures(failed)

          return results

      def _upload_single(self, resource: Resource, max_retries: int = 3) -> str:
          """단일 리소스 업로드 (재시도 포함)"""
          for attempt in range(max_retries):
              try:
                  return self.uploader.upload(resource.local_path, resource)
              except Exception as e:
                  if attempt == max_retries - 1:
                      raise
                  time.sleep(2 ** attempt)  # 지수 백오프
  ```

#### 4.3.2 업로드 캐시
- [x] `app/resources/upload_cache.py` - 중복 업로드 방지
  ```python
  import json
  from pathlib import Path

  class UploadCache:
      def __init__(self, cache_file: str = "data/checkpoint/upload_cache.json"):
          self.cache_file = Path(cache_file)
          self.cache = self._load()

      def _load(self) -> Dict[str, str]:
          if self.cache_file.exists():
              with open(self.cache_file, 'r') as f:
                  return json.load(f)
          return {}

      def get(self, hash_value: str) -> Optional[str]:
          return self.cache.get(hash_value)

      def set(self, hash_value: str, url: str):
          self.cache[hash_value] = url
          self._save()

      def _save(self):
          self.cache_file.parent.mkdir(parents=True, exist_ok=True)
          with open(self.cache_file, 'w') as f:
              json.dump(self.cache, f, indent=2)
  ```

#### 4.3.3 업로드 테스트
- [x] 냅킨경제학.enex (2 리소스) 업로드 테스트
- [x] IT트렌드.enex (21 리소스, 9가지 포맷) 업로드 테스트
- [x] 블랙야크.enex (68 리소스) 업로드 테스트

**완료 기준**:
- ✅ 100개 리소스 병렬 업로드 성공 (68 resources in large batch, 1,284 in full upload)
- ✅ 업로드 캐시 정상 작동 (Cache deduplication test passed - 62,601 files/sec)
- ✅ 실패율 5% 이하 (0% failure rate in all batch tests)

---

### Task 4.4: 블로그_예전모음.enex 처리 (4-6시간) ⚠️ 최종 보스 ✅ COMPLETED

- [x] 4.4.1 리소스 추출 (1,192개)
  - 메모리 사용량 모니터링
  - 디스크 공간 확인 (예상 500MB, 실제 112.68MB)

- [x] 4.4.2 배치 업로드 (100개씩 분할)
  - 진행률 실시간 표시
  - 중간 체크포인트 저장

- [x] 4.4.3 업로드 검증
  - 1,192개 모두 URL 확인
  - Public 접근 가능 확인
  - 실패 리소스 재시도

**완료 기준**: 1,192개 리소스 중 95% (1,132개) 이상 업로드 성공
**실제 결과**: ✅ **100% 성공 (1,192/1,192)** - 59.87초 소요, 0 실패

---

## Phase 5: 전체 마이그레이션 파이프라인 (2-3일)

### Task 5.1: 메인 실행 스크립트 작성 (4-6시간) ✅ COMPLETED (Partial - without Notion)

- [x] 5.1.1 `main.py` 생성
  ```python
  import argparse
  from pathlib import Path
  from tqdm import tqdm
  from app.parsers.enex_parser import EnexParser
  from app.notion.page_creator import PageCreator
  from app.resources.batch_uploader import BatchUploader
  from app.utils.checkpoint import CheckpointManager
  from app.utils.logger import setup_logger

  def main():
      parser = argparse.ArgumentParser()
      parser.add_argument('--file', help='특정 파일만 처리')
      parser.add_argument('--resume', action='store_true', help='체크포인트부터 재개')
      parser.add_argument('--dry-run', action='store_true', help='시뮬레이션')
      args = parser.parse_args()

      logger = setup_logger()
      checkpoint_mgr = CheckpointManager()

      # 소스 디렉토리
      source_dir = Path(os.getenv('ENEX_SOURCE_DIR'))

      # 파일 목록
      if args.file:
          files = [source_dir / args.file]
      else:
          files = list(source_dir.glob('*.enex'))

      # 체크포인트 로드
      if args.resume:
          processed_files = checkpoint_mgr.load_processed_files()
          files = [f for f in files if str(f) not in processed_files]

      # Notion 클라이언트
      notion_client = NotionClient(os.getenv('NOTION_API_KEY'))
      page_creator = PageCreator(notion_client, os.getenv('NOTION_PARENT_PAGE_ID'))

      # Uploader
      uploader = UploaderFactory.create(os.getenv('UPLOAD_STRATEGY'))
      batch_uploader = BatchUploader(uploader)

      # 파일별 처리
      for enex_file in tqdm(files, desc="Files"):
          logger.info(f"Processing {enex_file.name}")

          try:
              process_file(enex_file, page_creator, batch_uploader,
                          checkpoint_mgr, args.dry_run)
              checkpoint_mgr.mark_file_completed(str(enex_file))
          except Exception as e:
              logger.error(f"Failed to process {enex_file.name}: {e}")
              continue

  def process_file(enex_file, page_creator, batch_uploader,
                   checkpoint_mgr, dry_run=False):
      parser = EnexParser(str(enex_file))

      for note in parser.parse():
          # 체크포인트 확인
          if checkpoint_mgr.is_note_processed(note.title):
              continue

          # 리소스 업로드
          if note.resources:
              resource_map = batch_uploader.upload_resources(note.resources)
          else:
              resource_map = {}

          # Notion 페이지 생성
          if not dry_run:
              page_id = page_creator.create_from_note(note, resource_map)
              checkpoint_mgr.mark_note_completed(note.title, page_id)
  ```

- [x] 5.1.2 CLI 옵션 구현
  - ✅ `--file <파일명>`: 특정 파일만 처리
  - ✅ `--resume`: 체크포인트부터 재개
  - ✅ `--dry-run`: 실제 업로드 없이 시뮬레이션
  - ✅ `--verbose`: DEBUG 로깅
  - ✅ `--max-workers`: 병렬 작업자 수

**완료 기준**: ✅ CLI 실행 가능, 모든 옵션 작동 확인
**구현 완료**: main.py (285 lines), checkpoint.py (245 lines), logger.py (97 lines)
**테스트 결과**: 모든 CLI 옵션 정상 작동 (--file, --resume, --dry-run, --verbose)
**Note**: Notion API (Phase 3) 미구현으로 페이지 생성은 추후 통합 필요

---

### Task 5.2: 체크포인트 시스템 구현 (3-4시간) ✅ COMPLETED

- [x] 5.2.1 `app/utils/checkpoint.py` 생성 (Task 5.1과 함께 구현)
  ```python
  import json
  from datetime import datetime
  from pathlib import Path

  class CheckpointManager:
      def __init__(self, checkpoint_dir: str = "data/checkpoint"):
          self.checkpoint_dir = Path(checkpoint_dir)
          self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
          self.state_file = self.checkpoint_dir / "migration_state.json"
          self.state = self._load_state()

      def _load_state(self) -> dict:
          if self.state_file.exists():
              with open(self.state_file, 'r') as f:
                  return json.load(f)
          return {
              'started_at': None,
              'last_updated': None,
              'processed_files': [],
              'processed_notes': {},
              'failed_notes': [],
              'statistics': {
                  'total_notes': 0,
                  'successful_notes': 0,
                  'total_resources': 0,
                  'successful_resources': 0
              }
          }

      def mark_file_completed(self, file_path: str):
          self.state['processed_files'].append(file_path)
          self.state['last_updated'] = datetime.now().isoformat()
          self._save_state()

      def mark_note_completed(self, note_title: str, page_id: str):
          self.state['processed_notes'][note_title] = {
              'page_id': page_id,
              'completed_at': datetime.now().isoformat()
          }
          self.state['statistics']['successful_notes'] += 1
          self._save_state()

      def mark_note_failed(self, note_title: str, error: str):
          self.state['failed_notes'].append({
              'title': note_title,
              'error': error,
              'failed_at': datetime.now().isoformat()
          })
          self._save_state()

      def is_note_processed(self, note_title: str) -> bool:
          return note_title in self.state['processed_notes']

      def _save_state(self):
          with open(self.state_file, 'w') as f:
              json.dump(self.state, f, indent=2, ensure_ascii=False)
  ```

- [ ] 5.2.2 통계 수집
  - 처리된 노트 개수
  - 성공/실패 비율
  - 업로드된 리소스 개수
  - 예상 남은 시간

**완료 기준**: 중단 후 재개 시 이어서 처리

---

### Task 5.3: 로깅 시스템 구현 (2-3시간)

- [ ] 5.3.1 `app/utils/logger.py` 생성
  ```python
  import logging
  from pathlib import Path
  from datetime import datetime

  def setup_logger(log_dir: str = "data/logs"):
      log_dir = Path(log_dir)
      log_dir.mkdir(parents=True, exist_ok=True)

      # 로그 파일명 (날짜별)
      log_file = log_dir / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

      # 포맷터
      formatter = logging.Formatter(
          '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
      )

      # 파일 핸들러
      file_handler = logging.FileHandler(log_file, encoding='utf-8')
      file_handler.setFormatter(formatter)

      # 콘솔 핸들러
      console_handler = logging.StreamHandler()
      console_handler.setFormatter(formatter)

      # 루트 로거
      logger = logging.getLogger()
      logger.setLevel(logging.INFO)
      logger.addHandler(file_handler)
      logger.addHandler(console_handler)

      return logger
  ```

- [ ] 5.3.2 로깅 레벨 정의
  - INFO: 일반 진행 상황
  - WARNING: 리소스 업로드 실패 등
  - ERROR: 노트 처리 실패
  - DEBUG: 상세 디버깅 정보

**완료 기준**: 로그 파일 생성, 실시간 콘솔 출력

---

### Task 5.4: End-to-End 테스트 (4-6시간)

#### 5.4.1 Tier별 순차 테스트

- [ ] **Tier 1: 리소스 없음**
  ```bash
  python main.py --file "맛집.enex"
  python main.py --file "삶의태도.enex"
  ```
  - 예상 소요: 10초
  - 체크포인트: 텍스트 변환 정확도

- [ ] **Tier 2: 리소스 소량**
  ```bash
  python main.py --file "냅킨경제학.enex"  # 3 노트, 2 리소스
  python main.py --file "돌봄학개론.enex"  # 3 노트, 1 리소스
  ```
  - 예상 소요: 30초
  - 체크포인트: 이미지 업로드 성공

- [ ] **Tier 3: 중간 규모**
  ```bash
  python main.py --file "IT트렌드.enex"  # 45 노트, 21 리소스
  ```
  - 예상 소요: 5분
  - 체크포인트: 9가지 포맷 모두 처리

- [ ] **Tier 4: 대규모**
  ```bash
  python main.py --file "블랙야크.enex"  # 103 노트, 68 리소스
  ```
  - 예상 소요: 15분
  - 체크포인트: 대량 노트 처리

- [ ] **Tier 5: 최종 보스**
  ```bash
  python main.py --file "블로그_예전모음.enex"  # 60 노트, 1,192 리소스
  ```
  - 예상 소요: 1-2시간
  - 체크포인트: 1,192개 리소스 업로드

#### 5.4.2 중단/재개 테스트
- [ ] 중간에 Ctrl+C로 중단
- [ ] `--resume` 옵션으로 재개
- [ ] 체크포인트부터 이어서 처리 확인

#### 5.4.3 에러 시나리오 테스트
- [ ] 네트워크 끊김 시뮬레이션
- [ ] API 키 잘못된 경우
- [ ] 업로드 실패 시 재시도 확인

**완료 기준**:
- Tier 1-4 모두 100% 성공
- Tier 5 (블로그_예전모음) 95% 성공
- 중단/재개 정상 작동

---

### Task 5.5: 전체 마이그레이션 실행 (8-10시간) ⚠️ 장시간 실행

- [ ] 5.5.1 사전 준비
  - [ ] 디스크 공간 확인 (최소 5GB)
  - [ ] 네트워크 안정성 확인
  - [ ] Notion API 키 유효성 확인
  - [ ] 업로드 서비스 (S3/Cloudinary) 접근 확인

- [ ] 5.5.2 실행
  ```bash
  # 야간 실행 권장
  nohup python main.py > migration.log 2>&1 &

  # 또는 screen/tmux 사용
  screen -S evernote-migration
  python main.py
  ```

- [ ] 5.5.3 모니터링
  - [ ] 진행률 확인 (tqdm)
  - [ ] 로그 실시간 확인
  - [ ] 체크포인트 파일 주기적 확인
  - [ ] 메모리 사용량 모니터링

- [ ] 5.5.4 완료 후 검증
  - [ ] 총 노트 수 확인 (1,373개)
  - [ ] 총 리소스 수 확인 (1,574개)
  - [ ] 실패 노트 목록 확인
  - [ ] Notion 웹에서 샘플 확인 (각 Tier별 1개씩)

**완료 기준**:
- 1,373개 노트 중 95% (1,304개) 이상 성공
- 1,574개 리소스 중 90% (1,416개) 이상 성공

---

## Phase 6: 최적화 및 문서화 (1-2일)

### Task 6.1: 성능 최적화 (4-6시간)

- [ ] 6.1.1 병렬 처리 개선
  - [ ] 파일 단위 병렬 처리 고려 (조심: API 속도 제한)
  - [ ] 블록 배치 크기 최적화 (100개)

- [ ] 6.1.2 메모리 최적화
  - [ ] 대용량 파일 스트리밍 파싱 검증
  - [ ] 임시 파일 정리 (업로드 후 삭제)

- [ ] 6.1.3 이미지 최적화
  - [ ] 대용량 이미지 자동 리사이즈 (2000px)
  - [ ] WebP 변환 성능 개선

**완료 기준**: 블로그_예전모음.enex 처리 시간 50% 단축

---

### Task 6.2: CLI 개선 (2-3시간)

- [ ] 6.2.1 argparse 확장
  ```python
  parser.add_argument('--tier', type=int, choices=[1,2,3,4,5],
                      help='Tier별 처리 (1: 리소스 없음, 5: 최종 보스)')
  parser.add_argument('--stats', action='store_true',
                      help='통계만 출력')
  parser.add_argument('--validate', action='store_true',
                      help='Notion 페이지 검증')
  ```

- [ ] 6.2.2 통계 명령어
  ```bash
  python main.py --stats
  # 출력:
  # Total files: 23
  # Total notes: 1,373
  # Total resources: 1,574
  # Processed: 1,304 notes (95.0%)
  # Failed: 69 notes (5.0%)
  ```

**완료 기준**: 모든 CLI 옵션 작동 확인

---

### Task 6.3: 문서화 (3-4시간)

- [ ] 6.3.1 `README.md` 업데이트
  - [ ] 설치 방법
  - [ ] 설정 방법 (.env)
  - [ ] 사용 예제
  - [ ] 트러블슈팅

- [ ] 6.3.2 `USAGE.md` 작성
  ```markdown
  # 사용 가이드

  ## 1. 준비
  1. Notion Integration 생성
  2. 대상 페이지에 권한 부여
  3. .env 설정

  ## 2. 단계별 실행
  1. 테스트: python main.py --file "맛집.enex" --dry-run
  2. 소규모: python main.py --tier 2
  3. 전체: python main.py

  ## 3. 중단 후 재개
  Ctrl+C로 중단 후:
  python main.py --resume
  ```

- [ ] 6.3.3 Docstring 추가
  - [ ] 모든 클래스에 docstring
  - [ ] 모든 공개 메서드에 docstring
  - [ ] 타입 힌트 추가

**완료 기준**: README 작성 완료, docstring 100% 커버리지

---

### Task 6.4: 최종 테스트 및 릴리스 (2-3시간)

- [ ] 6.4.1 단위 테스트 작성
  ```bash
  pytest tests/ -v --cov=app --cov-report=html
  ```

- [ ] 6.4.2 통합 테스트
  - [ ] 전체 워크플로우 재실행 (샘플 파일)
  - [ ] 엣지 케이스 테스트

- [ ] 6.4.3 Git 커밋 및 릴리스
  ```bash
  git add .
  git commit -m "feat: Evernote to Notion migration tool v1.0"
  git tag v1.0.0
  git push origin main --tags
  ```

**완료 기준**:
- 테스트 커버리지 80% 이상
- README 완성
- Git 태그 생성

---

## 부록: Task 체크리스트 요약

### Phase 1: 환경 설정 및 파싱 (1-2일)
- [ ] 1.1 프로젝트 초기화 (2h)
- [ ] 1.2 ENEX 파서 개발 (4-6h)
- [ ] 1.3 파싱 테스트 (2-3h)
- [ ] 1.4 대용량 파일 검증 (1-2h)

### Phase 2: ENML 변환 (2-3일)
- [ ] 2.1 ENML 분석 (3-4h)
- [ ] 2.2 Markdown 변환기 (6-8h)
- [ ] 2.3 블록 빌더 (4-6h)
- [ ] 2.4 변환 테스트 (2-3h)

### Phase 3: Notion API (2일)
- [ ] 3.1 Integration 설정 (1h)
- [ ] 3.2 API 클라이언트 (4-6h)
- [ ] 3.3 페이지 생성기 (3-4h)
- [ ] 3.4 API 테스트 (2-3h)

### Phase 4: 리소스 처리 (3-4일) ⚠️
- [ ] 4.1 리소스 추출 (4-6h)
- [ ] 4.2 업로드 전략 구현 (1일)
- [ ] 4.3 대량 업로드 (6-8h)
- [ ] 4.4 블로그_예전모음 처리 (4-6h)

### Phase 5: 전체 파이프라인 (2-3일)
- [ ] 5.1 메인 스크립트 (4-6h)
- [ ] 5.2 체크포인트 (3-4h)
- [ ] 5.3 로깅 (2-3h)
- [ ] 5.4 E2E 테스트 (4-6h)
- [ ] 5.5 전체 실행 (8-10h)

### Phase 6: 최적화 및 문서화 (1-2일)
- [ ] 6.1 성능 최적화 (4-6h)
- [ ] 6.2 CLI 개선 (2-3h)
- [ ] 6.3 문서화 (3-4h)
- [ ] 6.4 최종 릴리스 (2-3h)

---

## 우선순위 Task (Critical Path)

1. **Task 1.2**: ENEX 파서 개발 (모든 것의 기반)
2. **Task 2.2**: ENML 변환기 (핵심 로직)
3. **Task 3.2**: Notion API 클라이언트 (연동 필수)
4. **Task 4.2**: 업로드 전략 구현 ⚠️ (가장 큰 난제)
5. **Task 5.5**: 전체 마이그레이션 실행 (최종 목표)

---

**작성일**: 2025-10-25
**총 Task 수**: 80+
**예상 총 작업 시간**: 90-130시간 (개발 11-16일 + 실행 8-10시간)
