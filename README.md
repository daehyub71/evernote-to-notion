# Evernote to Notion Migration Tool

**에버노트 노트북(.enex)을 노션(Notion) 개인 페이지로 자동 마이그레이션하는 파이썬 프로그램**

## 프로젝트 개요

### 데이터 규모 (실제 분석 결과)
- **ENEX 파일**: 23개
- **총 노트**: 1,373개
- **총 리소스**: 1,574개 (이미지 1,557개, 문서 13개, 텍스트 4개)
- **총 용량**: ~450MB

### 주요 기능
- ENEX XML 파싱 및 ENML → Markdown 변환
- 1,574개 리소스 자동 업로드 (9가지 포맷 지원)
- MD5 해시 기반 리소스 매칭
- Notion API 연동 (페이지 생성, 블록 추가)
- 체크포인트 시스템 (중단/재개 지원)
- 진행률 표시 및 에러 로깅

## 지원 포맷

### 노트 요소
- ✅ 텍스트, 제목 (h1-h6)
- ✅ 리스트 (ul, ol)
- ✅ 체크박스 (`<en-todo>`)
- ✅ 링크, 굵게, 기울임
- ✅ 코드블록

### 리소스 (첨부파일)
- ✅ **이미지**: JPEG, PNG, SVG, WebP
- ✅ **문서**: PDF, DOCX, PPTX
- ✅ **텍스트**: Markdown, Plain Text

## 프로젝트 구조

```
evernote-to-notion/
├── PROJECT_PLAN.md             # 상세 개발 계획서
├── ENEX_ANALYSIS.md            # 실제 데이터 분석 결과
├── README.md                   # 이 문서
├── .env.example                # 환경변수 템플릿
├── requirements.txt
├── main.py                     # 메인 실행 스크립트
├── app/
│   ├── parsers/
│   │   ├── enex_parser.py      # ENEX XML 파싱
│   │   └── enml_converter.py   # ENML → Markdown 변환
│   ├── notion/
│   │   ├── client.py           # Notion API 클라이언트
│   │   ├── page_creator.py     # 페이지 생성
│   │   └── block_builder.py    # 블록 구성
│   ├── resources/
│   │   ├── resource_extractor.py  # 리소스 추출
│   │   ├── image_handler.py    # 이미지 처리
│   │   └── uploader.py         # S3/Cloudinary 업로드
│   └── utils/
│       ├── logger.py
│       └── rate_limiter.py     # API 속도 제한 관리
├── scripts/
│   ├── test_enex_parse.py      # ENEX 파싱 테스트
│   └── test_notion_api.py      # Notion API 연결 테스트
└── data/
    ├── temp/                   # 임시 이미지 저장
    ├── logs/                   # 로그 파일
    └── checkpoint/             # 진행 상황 체크포인트
```

## 개발 계획

### 6단계 개발 로드맵

| Phase | 작업 내용 | 예상 기간 |
|-------|----------|---------|
| **Phase 1** | 환경 설정 및 ENEX 파싱 | 1-2일 |
| **Phase 2** | ENML → Notion 변환 | 2-3일 |
| **Phase 3** | Notion API 연동 | 2일 |
| **Phase 4** | 리소스 처리 ⚠️ | 3-4일 |
| **Phase 5** | 전체 파이프라인 | 2-3일 |
| **Phase 6** | 최적화 및 문서화 | 1-2일 |
| **합계** | | **11-16일** |

**실행 시간**: 전체 마이그레이션 약 8-10시간 (Notion API 속도 제한)

## 주요 기술 도전과제

### 1. 대량 리소스 업로드 (1,574개) ⚠️ 최대 난제
- **문제**: Notion API는 Base64 직접 업로드 불가, 외부 URL만 허용
- **해결**: AWS S3 또는 Cloudinary 사용
- **특이점**: 블로그_예전모음.enex 하나에 1,192개 (75.7%)

### 2. API 속도 제한
- **문제**: Notion API 초당 3회 제한 → 최소 8-10시간 소요
- **해결**: Rate limiter + 체크포인트 시스템

### 3. 다양한 파일 포맷 (9가지)
- **해결**: 포맷별 핸들러 구현, WebP → PNG 변환

### 4. MD5 해시 매칭
- **메커니즘**: ENML `<en-media hash="34c08f...">` ↔ 리소스 MD5
- **해결**: 해시 딕셔너리 사전 구축 (O(1) 조회)

## 상세 문서

- **[PROJECT_PLAN.md](PROJECT_PLAN.md)**: 완전한 개발 계획서 (기술 분석, 아키텍처, 단계별 체크리스트)
- **[ENEX_ANALYSIS.md](ENEX_ANALYSIS.md)**: 실제 ENEX 파일 분석 결과 (파일별 통계, 리소스 분포)

## 개발 상태

🚧 **현재 상태**: 계획 수립 완료 (2025-10-25)

**완료**:
- ✅ ENEX 파일 실제 데이터 분석
- ✅ 상세 개발 계획서 작성
- ✅ 기술적 도전과제 파악

**다음 단계**:
- [ ] Phase 1: 환경 설정 및 ENEX 파싱

## 라이선스

MIT License

---

**작성**: 2025-10-25
**작성자**: Claude Code
