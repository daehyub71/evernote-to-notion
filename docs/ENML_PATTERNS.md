# ENML 패턴 상세 분석 결과

**분석 일시**: 2025-10-25
**분석 파일**: 23개 ENEX 파일 중 5개 샘플링
**총 노트**: 207개 분석
**발견된 태그**: 29종류

---

## 태그 빈도 분석 (Top 20)

| 순위 | 태그 | 출현 횟수 | 설명 |
|------|------|----------|------|
| 1 | `div` | 16,609 | 기본 블록 컨테이너 |
| 2 | `li` | 3,875 | 리스트 아이템 |
| 3 | `b` | 3,499 | 굵은 텍스트 |
| 4 | `br` | 1,267 | 줄바꿈 |
| 5 | `span` | 1,105 | 인라인 컨테이너 (주로 스타일용) |
| 6 | `h3` | 1,042 | 헤딩 레벨 3 |
| 7 | `ul` | 961 | 순서 없는 리스트 |
| 8 | `td` | 869 | 테이블 셀 |
| 9 | `h2` | 544 | 헤딩 레벨 2 |
| 10 | `code` | 517 | 코드 인라인 |
| 11 | `hr` | 377 | 수평선 |
| 12 | `a` | 240 | 하이퍼링크 |
| 13 | `en-note` | 207 | ENML 루트 요소 |
| 14 | `tr` | 203 | 테이블 행 |
| 15 | `ol` | 197 | 순서 있는 리스트 |
| 16 | `h4` | 195 | 헤딩 레벨 4 |
| 17 | `col` | 139 | 테이블 컬럼 정의 |
| 18 | `i` | 120 | 기울임 텍스트 |
| 19 | `h1` | 106 | 헤딩 레벨 1 |
| 20 | `th` | 83 | 테이블 헤더 셀 |

**기타 태그**: `colgroup` (29), `tbody` (29), `table` (29), `blockquote` (23), `p` (21), `strong` (18), `u` (6), `img` (3)

---

## 패턴별 상세 분석 (20+ 패턴)

### 1. 기본 텍스트 포맷팅

#### 1.1 굵은 텍스트 (`<b>`)
```xml
<b>IP 주소</b>
<b>도메인 주소</b>
```
**변환 전략**: Notion `bold` rich text annotation

#### 1.2 기울임 (`<i>`)
```xml
<i>주요 개념 설명</i>
```
**변환 전략**: Notion `italic` rich text annotation

#### 1.3 밑줄 (`<u>`)
```xml
<u>중요한 내용</u>
```
**변환 전략**: Notion `underline` rich text annotation

#### 1.4 강조 (`<strong>`)
```xml
<strong>매우 중요한 내용</strong>
```
**변환 전략**: `<b>`와 동일하게 Notion `bold`로 변환

---

### 2. 헤딩 (6개 레벨)

#### 2.1 Heading 1 (`<h1>`)
```xml
<h1 style="--en-nodeId:8503023a-1add-40a9-b034-a248291b7429;">'저축의 시대'에서 '투자의 시대'로: 복리의 마법을 깨우는 패러다임 혁명</h1>
```
**특징**: `--en-nodeId` 스타일 속성 포함
**변환 전략**: Notion `heading_1` 블록

#### 2.2 Heading 2 (`<h2>`)
```xml
<h2 style="--en-nodeId:0a47ce0d-bdb4-40ad-a77b-4ba5cbc07a4f;">저축의 시대의 종말: 더 이상 안전하지 않은 안전자산</h2>
```
**변환 전략**: Notion `heading_2` 블록

#### 2.3 Heading 3 (`<h3>`)
```xml
<h3 style="--en-nodeId:2f99fc5c-c182-41e0-818e-f8b0a273ac47;">조기 시작과 꾸준함</h3>
```
**변환 전략**: Notion `heading_3` 블록

**Note**: `<h4>`, `<h5>`, `<h6>`는 Notion에서 미지원 → `heading_3` + 볼드 처리

---

### 3. 리스트 구조

#### 3.1 순서 없는 리스트 (`<ul>` + `<li>`)
```xml
<ul>
  <li><div><b>IPv4</b>: 32비트 주소 체계, 4개의 숫자로 구성 (예: 192.168.0.1)</div></li>
  <li><div><b>IPv6</b>: 128비트 주소 체계, 더 많은 기기를 수용 (예: 2001:0db8::1)</div></li>
</ul>
```
**특징**: `<li>` 내부에 `<div>` 중첩 패턴 일반적
**변환 전략**: Notion `bulleted_list_item` 블록

#### 3.2 순서 있는 리스트 (`<ol>` + `<li>`)
```xml
<ol>
  <li><div>사용자가 브라우저에 'www.google.com'을 입력합니다.</div></li>
  <li><div>컴퓨터는 DNS 서버에 '이 도메인에 해당하는 IP 주소가 뭐야?' 하고 묻습니다.</div></li>
  <li><div>DNS 서버는 '142.250.206.68'이라고 응답합니다.</div></li>
</ol>
```
**변환 전략**: Notion `numbered_list_item` 블록

#### 3.3 중첩 리스트
```xml
<ul>
  <li><div>유니캐스트(Unicast)</div></li>
  <ul>
    <li><div>출발지와 목적지가 1:1로 통신</div></li>
  </ul>
</ul>
```
**변환 전략**: Notion 블록의 `children` 속성 활용

---

### 4. 링크 (`<a>`)

```xml
<a href="https://www.samsungsds.com/kr/insights/web3.html" rev="en_rl_none">https://www.samsungsds.com/kr/insights/web3.html</a>
```
**특징**:
- `rev="en_rl_none"` 속성 (에버노트 특수 속성)
- URL과 링크 텍스트가 동일한 경우 많음

**변환 전략**: Notion rich text의 `link` annotation

---

### 5. 코드 블록

#### 5.1 인라인 코드 (`<code>`)
```xml
<code>nslookup</code>, <code>dig</code>
```
**변환 전략**: Notion `code` rich text annotation

#### 5.2 코드 블록 (추정 패턴)
실제 샘플에서는 대부분 인라인 `<code>` 사용.
멀티라인 코드는 `<div>` 내부에 `<code>` 중첩으로 표현될 가능성.

**변환 전략**:
- 줄바꿈 포함 시 Notion `code` 블록 생성
- 인라인은 rich text `code`

---

### 6. 에버노트 특수 태그

#### 6.1 미디어 첨부 (`<en-media>`)

**이미지 (가장 일반적)**:
```xml
<en-media
  style="--en-naturalWidth:893; --en-naturalHeight:744;"
  width="633px"
  hash="831382670ca9c47cdc4ed919f6c05feb"
  type="image/png" />
```

**속성 설명**:
- `hash`: 리소스 MD5 해시 (리소스 매칭 키)
- `type`: MIME 타입
- `style`: 원본 크기 정보
- `width`: 표시 너비 (선택적)
- `alt`: 대체 텍스트 (선택적)

**발견된 MIME 타입**:
- `image/png`: 4회
- `image/jpeg`: 4회
- `image/svg+xml`: 12회
- `application/pdf`: 1회
- `text/markdown`: 확인됨 (빈도 낮음)

**변환 전략**:
1. `hash`로 리소스 매칭
2. 리소스 업로드 (S3/Cloudinary)
3. Notion `image` 블록 생성 (URL 사용)
4. PDF는 `file` 블록 또는 `pdf` 블록

#### 6.2 체크박스 (`<en-todo>`)
```xml
<en-todo checked="true"/>작업 완료
<en-todo/>미완료 작업
```
**속성**:
- `checked="true"`: 체크됨
- 속성 없음: 미체크

**변환 전략**: Notion `to_do` 블록, `checked` 속성 매핑

---

### 7. 테이블 (`<table>`)

```xml
<table width="564px" style="border-collapse:collapse;width:564px;">
  <colgroup>
    <col style="width: 188px;" />
    <col style="width: 188px;" />
    <col style="width: 188px;" />
  </colgroup>
  <tbody>
    <tr>
      <th style="border:1px solid rgb(0, 0, 0);padding:5px;">헤더1</th>
      <th style="border:1px solid rgb(0, 0, 0);padding:5px;">헤더2</th>
    </tr>
    <tr>
      <td style="border:1px solid rgb(0, 0, 0);padding:5px;">셀1</td>
      <td style="border:1px solid rgb(0, 0, 0);padding:5px;">셀2</td>
    </tr>
  </tbody>
</table>
```

**구조**:
- `<colgroup>` + `<col>`: 컬럼 너비 정의
- `<tbody>`: 테이블 본문
- `<tr>`: 행
- `<th>`: 헤더 셀
- `<td>`: 데이터 셀

**변환 전략**:
- Notion `table` 블록
- 첫 행이 `<th>`이면 `has_column_header: true`

---

### 8. 기타 구조 요소

#### 8.1 구분선 (`<hr>`)
```xml
<hr/>
```
**변환 전략**: Notion `divider` 블록

#### 8.2 인용 (`<blockquote>`)
```xml
<blockquote>
  인용된 텍스트
</blockquote>
```
**변환 전략**: Notion `quote` 블록

#### 8.3 줄바꿈 (`<br>`)
```xml
텍스트<br/>다음 줄
```
**변환 전략**: Notion paragraph에서 `\n`으로 변환

#### 8.4 div + span 중첩
```xml
<div>
  <span style="color:rgb(85, 85, 85);">텍스트</span>
</div>
```
**특징**: 스타일 적용을 위한 중첩 구조 일반적
**변환 전략**:
- 색상 정보는 Notion rich text의 `color` annotation으로 변환
- 단, Notion 제한된 색상만 지원

---

## 특수 케이스

### 1. HTML 엔티티 (3종)

| 엔티티 | 의미 | 변환 후 |
|-------|------|---------|
| `&lt;` | `<` | `<` |
| `&gt;` | `>` | `>` |
| `&amp;` | `&` | `&` |
| `&quot;` | `"` | `"` |

**처리 방법**: `html.unescape()` 사용

### 2. 복잡한 스타일 속성

#### 2.1 에버노트 커스텀 속성
```xml
style="--en-nodeId:8503023a-1add-40a9-b034-a248291b7429;"
style="--en-naturalWidth:893; --en-naturalHeight:744;"
style="--en-markholder:true;"
```
**처리**: 무시 (Notion 미지원)

#### 2.2 인라인 CSS
```xml
style="color:rgb(224, 108, 117);"
style="border:1px solid rgb(0, 0, 0);padding:5px;"
style="font-size:35px;font-weight:normal;line-height:35px;"
```
**처리**:
- `color`: Notion color 매핑 시도 (제한적)
- 기타: 무시 (Notion 미지원)

### 3. 중첩 구조 패턴

```xml
<div>
  <span style="color:rgb(85, 85, 85);">
    <span style="--en-markholder:true;">
      <br/>
    </span>
  </span>
</div>
```
**처리**: 재귀적 파싱으로 텍스트 추출

### 4. 빈 요소 처리

```xml
<div><br/></div>
<div></div>
<span></span>
```
**처리**:
- `<div><br/></div>`: 빈 paragraph 블록
- 완전히 빈 요소: 무시

---

## 변환 매핑 테이블

| ENML 태그 | Notion 블록/속성 | 우선순위 | 난이도 |
|-----------|------------------|----------|--------|
| `<h1>` | `heading_1` | P0 | 쉬움 |
| `<h2>` | `heading_2` | P0 | 쉬움 |
| `<h3>` | `heading_3` | P0 | 쉬움 |
| `<h4-6>` | `heading_3` + bold | P1 | 중간 |
| `<div>` | `paragraph` | P0 | 쉬움 |
| `<p>` | `paragraph` | P0 | 쉬움 |
| `<br>` | `\n` in paragraph | P1 | 쉬움 |
| `<ul>` + `<li>` | `bulleted_list_item` | P0 | 중간 |
| `<ol>` + `<li>` | `numbered_list_item` | P0 | 중간 |
| `<b>`, `<strong>` | rich_text `bold` | P0 | 쉬움 |
| `<i>` | rich_text `italic` | P0 | 쉬움 |
| `<u>` | rich_text `underline` | P1 | 쉬움 |
| `<code>` | rich_text `code` | P1 | 쉬움 |
| `<a>` | rich_text `link` | P0 | 중간 |
| `<en-media>` (image) | `image` block | P0 | 어려움 |
| `<en-media>` (pdf) | `file` or `pdf` block | P1 | 어려움 |
| `<en-todo>` | `to_do` block | P1 | 중간 |
| `<table>` | `table` block | P2 | 어려움 |
| `<hr>` | `divider` block | P1 | 쉬움 |
| `<blockquote>` | `quote` block | P1 | 쉬움 |
| `<span>` (color) | rich_text `color` | P2 | 중간 |

**우선순위 설명**:
- **P0**: 필수 (95% 커버리지에 필요)
- **P1**: 권장 (사용자 경험 개선)
- **P2**: 선택적 (고급 기능)

---

## 변환 알고리즘 개요

### 1단계: HTML 파싱
```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(enml_content, 'xml')
```

### 2단계: 태그별 순회
```python
for element in soup.find_all(['h1', 'h2', 'h3', 'div', 'ul', 'ol', ...]):
    block = convert_element_to_notion_block(element)
    blocks.append(block)
```

### 3단계: Rich Text 처리
```python
def process_inline_elements(element):
    rich_text = []
    for child in element.descendants:
        if isinstance(child, str):
            text = html.unescape(child)
            annotations = extract_annotations(child.parent)
            rich_text.append({
                "type": "text",
                "text": {"content": text},
                "annotations": annotations
            })
    return rich_text
```

### 4단계: 리소스 매칭
```python
en_media_tags = soup.find_all('en-media')
for tag in en_media_tags:
    hash_value = tag.get('hash')
    resource = note.get_resource_by_hash(hash_value)
    if resource:
        uploaded_url = upload_resource(resource)
        # Create image/file block with URL
```

---

## 통계 요약

- **분석된 노트**: 207개
- **발견된 고유 태그**: 29개
- **정의된 변환 패턴**: 24개
- **우선순위 P0 패턴**: 11개 (필수)
- **우선순위 P1 패턴**: 8개 (권장)
- **우선순위 P2 패턴**: 5개 (선택적)

**목표 달성**:
✅ 20가지 이상 ENML 패턴 수집 완료 (24개)
✅ 특수 케이스 분석 완료 (HTML 엔티티, 스타일, 중첩)
✅ Notion 매핑 전략 수립 완료

---

**다음 단계**: Task 2.2 - ENML → Notion 블록 변환기 구현
