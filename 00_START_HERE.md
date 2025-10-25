# 🚀 시작 가이드 - Evernote to Notion Migration

**환영합니다!** 이 프로젝트는 에버노트 노트를 노션으로 마이그레이션하는 도구입니다.

---

## 📚 문서 읽는 순서

### 1️⃣ 먼저 읽을 문서

**[README.md](README.md)** - 프로젝트 개요 (5분)
- 프로젝트가 무엇인지
- 데이터 규모 (1,373개 노트, 1,574개 리소스)
- 주요 기능
- 기술적 도전과제

### 2️⃣ 데이터 이해하기

**[ENEX_ANALYSIS.md](ENEX_ANALYSIS.md)** - 실제 데이터 분석 결과 (10분)
- 23개 ENEX 파일 상세 통계
- 파일별 노트/리소스 분포
- MIME 타입 분석 (9가지 포맷)
- 처리 우선순위 (Tier 1-5)

**핵심 발견**:
- 블로그_예전모음.enex 하나에 **1,192개 리소스** (전체의 75.7%)
- 98.9%가 이미지 (JPEG, PNG)
- 예상 처리 시간: **8-10시간**

---

## 🛠️ 개발 시작하기

### 3️⃣ 개발 계획 이해하기

**[PROJECT_PLAN.md](PROJECT_PLAN.md)** - 완전한 개발 계획서 (30분)
- 기술 분석 (ENEX 구조, Notion API)
- 시스템 설계 (아키텍처, 디렉토리 구조)
- 6단계 개발 로드맵 (Phase 1-6)
- 데이터 모델
- 기술적 도전과제 및 해결방안

**언제 읽나요?**
- 개발 시작 전 전체 그림 이해
- 기술 결정 시 참고 (예: 파일 업로드 전략)
- 막혔을 때 해결 방안 찾기

### 4️⃣ 실제 작업하기

**[TASKS.md](TASKS.md)** - 상세 Task 목록 (작업 중 항상 참조)
- **80+ Task 목록** (Phase별 분류)
- 각 Task별 상세 구현 가이드
- 코드 스니펫 포함
- 완료 기준 명확화

**구성**:
```
Phase 1: 환경 설정 및 ENEX 파싱
  └─ Task 1.1: 프로젝트 초기화 (2시간)
     ├─ 1.1.1 디렉토리 구조 생성
     ├─ 1.1.2 Git 저장소 초기화
     ├─ 1.1.3 requirements.txt 작성
     └─ 1.1.4 가상환경 생성
  └─ Task 1.2: ENEX 파서 개발 (4-6시간)
     ├─ 1.2.1 EnexParser 클래스 구현
     ├─ 1.2.2 데이터 모델 정의
     └─ 1.2.3 날짜/시간 파싱
  ...
```

**사용법**:
1. Task를 순서대로 진행
2. 각 Task의 코드 스니펫 참고
3. 완료 시 체크박스 체크
4. 막히면 PROJECT_PLAN.md 참조

### 5️⃣ 진행 상황 추적하기

**[CHECKLIST.md](CHECKLIST.md)** - 빠른 체크리스트 (매일 확인)
- Phase별 핵심 항목만 요약
- 진행 상황 빠르게 확인
- Daily Standup용

**언제 사용하나요?**
- 매일 아침: 오늘 할 일 확인
- 매일 저녁: 완료 항목 체크
- 막혔을 때: 빠뜨린 항목 찾기

---

## ⚡ 빠른 시작 (Quick Start)

### 단계 1: 프로젝트 초기화 (10분)

```bash
# 1. 디렉토리 구조 생성
cd /Users/sunchulkim/src/evernote-to-notion
mkdir -p app/{parsers,notion,resources,utils}
mkdir -p scripts data/{temp,logs,checkpoint} tests

# 2. 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 3. 의존성 설치 (requirements.txt 먼저 작성 필요)
pip install -r requirements.txt

# 4. .env 파일 생성
cp .env.example .env
# .env 파일 편집 (Notion API 키 등)
```

### 단계 2: Phase 1 시작 (오늘의 목표)

**[TASKS.md](TASKS.md)의 Task 1.1-1.2를 진행하세요**

체크포인트:
- [ ] 디렉토리 구조 생성 완료
- [ ] Git 초기화 완료
- [ ] 가상환경 설정 완료
- [ ] EnexParser 클래스 뼈대 작성

### 단계 3: 첫 테스트 (오늘 저녁 목표)

```bash
# 맛집.enex 파싱 테스트
python scripts/test_enex_parse.py --file "맛집.enex"

# 예상 출력:
# File: 맛집.enex
# Notes: 3
# Resources: 0
# ✅ Success!
```

---

## 📊 프로젝트 규모 (한눈에 보기)

### 입력 데이터
```
📁 /Users/sunchulkim/evernote/
├── 📄 23개 ENEX 파일
├── 📝 1,373개 노트
├── 🖼️ 1,574개 리소스
│   ├── JPEG: 1,383개 (87.9%)
│   ├── PNG: 160개 (10.2%)
│   ├── PDF: 11개
│   └── 기타: 20개
└── 💾 ~450MB

⚠️ 최대 난제: 블로그_예전모음.enex
   - 160MB 파일
   - 1,192개 리소스 (전체의 75.7%)
```

### 개발 규모
```
🛠️ 개발 단계: 6 Phase
📋 총 Task: 80+ 개
⏱️ 예상 기간: 11-16일
💻 코드 라인: ~3,000 라인 (예상)
🚀 실행 시간: 8-10시간 (전체 마이그레이션)
```

### 성공 기준
```
✅ 노트 성공률: 95% (1,304/1,373)
✅ 리소스 성공률: 90% (1,416/1,574)
✅ 데이터 손실: 0% (텍스트 100% 보존)
```

---

## 🎯 Phase별 목표

| Phase | 목표 | 예상 기간 | 핵심 난이도 |
|-------|------|-----------|-------------|
| **Phase 1** | ENEX 파싱 성공 | 1-2일 | ⭐⭐ 보통 |
| **Phase 2** | ENML → Notion 변환 | 2-3일 | ⭐⭐⭐ 어려움 |
| **Phase 3** | Notion API 연동 | 2일 | ⭐⭐ 보통 |
| **Phase 4** | 리소스 업로드 ⚠️ | 3-4일 | ⭐⭐⭐⭐⭐ 최고 난이도 |
| **Phase 5** | 전체 파이프라인 | 2-3일 | ⭐⭐⭐ 어려움 |
| **Phase 6** | 최적화 및 문서화 | 1-2일 | ⭐ 쉬움 |

**Critical Path**: Phase 4 (리소스 업로드)
- 1,574개 파일을 어디에 호스팅?
- AWS S3 vs Cloudinary vs Imgur 결정 필요
- 블로그_예전모음.enex (1,192개 리소스) 처리

---

## 💡 핵심 기술 결정 사항

### 결정 1: 파일 업로드 전략 (Phase 4.2에서 결정)

| 옵션 | 장점 | 단점 | 비용 | 권장 |
|------|------|------|------|------|
| **AWS S3** | 안정적, 빠름 | 설정 복잡 | $1-2/월 | ⭐⭐⭐⭐⭐ |
| **Cloudinary** | 무료 25GB | 이미지만 | 무료 | ⭐⭐⭐⭐ |
| **Imgur** | 무료, 간단 | 불안정, 이미지만 | 무료 | ⭐⭐ |

**권장**: AWS S3 (안정성 최우선)

### 결정 2: 처리 순서 (Phase 5.4)

**Tier별 순차 처리 권장**:
1. Tier 1-2: 검증 (리소스 없음/소량)
2. Tier 3-4: 본격 처리 (중간/대규모)
3. Tier 5: 최종 보스 (블로그_예전모음.enex)

**왜 순차적으로?**
- 작은 파일로 먼저 검증
- 문제 발생 시 빠른 수정
- 블로그_예전모음 실패 시 영향 최소화

---

## 🔧 자주 참조할 코드 위치

### 데이터 모델
```
app/models.py
├── EvernoteNote (노트 구조)
└── Resource (리소스 구조)
```

### 핵심 로직
```
app/parsers/enex_parser.py      # ENEX XML 파싱
app/parsers/enml_converter.py   # ENML → Notion 블록 변환
app/notion/client.py             # Notion API 호출
app/resources/batch_uploader.py # 대량 리소스 업로드
main.py                          # 전체 워크플로우
```

### 설정 파일
```
.env                    # API 키, 설정
requirements.txt        # 의존성
data/checkpoint/*.json  # 진행 상황
```

---

## 🆘 도움이 필요할 때

### 막혔을 때 참조 순서

1. **[TASKS.md](TASKS.md)** - 해당 Task의 코드 스니펫 확인
2. **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - 기술적 도전과제 섹션 참조
3. **[ENEX_ANALYSIS.md](ENEX_ANALYSIS.md)** - 데이터 구조 재확인
4. **로그 파일** - `data/logs/` 확인
5. **체크포인트** - `data/checkpoint/migration_state.json` 확인

### 자주 발생할 문제

| 문제 | 해결 방법 | 참고 문서 |
|------|----------|----------|
| ENEX 파싱 에러 | lxml 스트리밍 파싱 사용 | TASKS.md Task 1.2.1 |
| Notion API 429 에러 | Rate Limiter 확인 | TASKS.md Task 3.2.2 |
| 리소스 업로드 실패 | 재시도 로직, 로그 확인 | TASKS.md Task 4.3.1 |
| 메모리 부족 | 스트리밍 파싱, 임시 파일 삭제 | PROJECT_PLAN.md 4장 |

---

## 📅 권장 일정 (예시)

### Week 1: Phase 1-2
- **Day 1**: 프로젝트 초기화, ENEX 파서 (Task 1.1-1.2)
- **Day 2**: 파싱 테스트, 대용량 파일 검증 (Task 1.3-1.4)
- **Day 3**: ENML 분석, 변환기 시작 (Task 2.1-2.2)
- **Day 4**: 변환기 완성 (Task 2.2)
- **Day 5**: 블록 빌더, 테스트 (Task 2.3-2.4)

### Week 2: Phase 3-4
- **Day 6**: Notion Integration 설정, API 클라이언트 (Task 3.1-3.2)
- **Day 7**: 페이지 생성기, 테스트 (Task 3.3-3.4)
- **Day 8**: 리소스 추출, **업로드 전략 결정** ⚠️ (Task 4.1-4.2)
- **Day 9**: 대량 업로드 구현 (Task 4.3)
- **Day 10**: 블로그_예전모음 처리 (Task 4.4)

### Week 3: Phase 5-6
- **Day 11**: 메인 스크립트, 체크포인트 (Task 5.1-5.2)
- **Day 12**: 로깅, E2E 테스트 (Task 5.3-5.4)
- **Day 13**: **전체 실행** (야간 8-10시간) (Task 5.5)
- **Day 14**: 최적화, 문서화 (Task 6.1-6.3)
- **Day 15**: 최종 테스트, 릴리스 (Task 6.4)

---

## ✅ 시작 전 체크리스트

프로젝트를 시작하기 전에 다음을 확인하세요:

- [ ] 모든 문서 읽음 (README, ENEX_ANALYSIS, PROJECT_PLAN)
- [ ] 개발 환경 준비 (Python 3.11+, Git)
- [ ] 디스크 공간 확인 (최소 5GB)
- [ ] Notion 계정 보유
- [ ] AWS 계정 보유 (S3 사용 시) 또는 Cloudinary 계정
- [ ] 시간 확보 (최소 11-16일 + 실행 8-10시간)

---

## 🎉 성공적인 마이그레이션을 위한 팁

1. **작은 파일부터 시작** - Tier 1, 2부터 검증
2. **체크포인트 자주 확인** - 진행 상황 수시 저장
3. **로그 모니터링** - 에러 조기 발견
4. **야간 실행** - Phase 5.5는 자고 일어나면 완료
5. **백업** - 원본 ENEX 파일 절대 삭제 금지

---

**시작 준비 되셨나요?** 👉 [TASKS.md](TASKS.md) Phase 1부터 시작하세요!

**궁금한 점이 있다면?** 👉 [PROJECT_PLAN.md](PROJECT_PLAN.md) 참조

**행운을 빕니다!** 🚀

---

**작성일**: 2025-10-25
**버전**: 1.0
