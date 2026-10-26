# RAG Dataset Builder Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. The user authorized implementation and public commits/pushes. No additional execution-method approval is needed.

**Goal:** 사용자 질문으로 시작해 다양한 원본의 평가 가능성을 판정하고 근거를 보존한 평가셋을 생성하는 스킬을 제공한다.

**Architecture:** 에이전트가 접수·분석·생성·의미 검토를 수행한다. Python 표준 라이브러리 CLI는 계약·참조·검토 상태를 검증하고 새 파일로 동결한다. CLI는 원본 파싱·생성·성능 채점을 대신하지 않는다.

**Tech Stack:** Markdown skill, Python 3.10+ standard library, unittest, GitHub Actions.

**Spec:** [plan.md](plan.md)

## Global Constraints

- 전역 플러그인·기존 rag-eval 코드를 수정하지 않는다.
- 새 런타임 의존성·생성 API·OCR 엔진·웹 UI를 추가하지 않는다.
- 예제는 합성 자료만 포함한다. 고객 데이터·로그·키를 공개 저장소에 넣지 않는다.
- 동결 파일은 덮어쓰지 않는다. 동결은 구조·선언 검사이며 정답 진위나 독립성을 증명하지 못한다.

## Review Focus

- 검색 전용 문항에 답변 정답을 강제하지 않는가.
- 문자열·빈 값·bool-as-int·비정상 숫자가 라벨/좌표/크기 필드에 들어올 때 거절하는가.
- 대체 근거(OR)와 결합 근거(AND)를 변환·평탄화하지 않는가.
- source/query 분리 정책이 실제 긍정 근거에 적용되는가.
- 손상 JSON·기존 출력·미검토 항목이 성공으로 동결되지 않는가.

## Task 1: 계획과 공개 저장소

**Files:** `docs/plan.md`, `docs/review.md`, `docs/implementation-plan.md`, `.gitignore`.

- [x] 계획의 타당성 반례를 검토하고 독립 검토의 네 가지 빈 조건을 보완한다.
- [x] 계획 문서의 링크·경로와 공개 대상 파일을 확인하고 첫 커밋·push를 수행한다.

## Task 2: 스킬과 계약

**Files:** `skills/rag-dataset-builder/SKILL.md`, `references/contract.md`, `references/data-types.md`.

**Interfaces:** contract v1 JSON bundle (`manifest`, `evidence`, `items`), validate/freeze CLI를 Task 3에서 구현한다.

- [x] 신규 스킬 없는 행동 기준선을 실행해 질문 누락을 관찰한다.
- [x] 접수·분석·지원 판정·평가 설계·파일럿·검토·동결·측정 연결 절차를 쓴다.
- [x] 필드 타입·필수 조건·근거 위치·동결 기준을 계약에 명시한다.
- [x] 스킬 포맷 검증과 새 컨텍스트 행동 검사를 수행한다. 성공 조건: 문항 생성 전 데이터/사용 과업 질문, 벡터-only 중단, 검색/답변 구별, 대체 근거 보존.
- [x] 스킬·계약을 별도 커밋·push한다.

## Task 3: 검증기와 재현 가능한 예제

**Files:** `skills/rag-dataset-builder/scripts/dataset.py`, `examples/toy/dataset.json`, `tests/test_dataset.py`.

**Interfaces:** `validate_dataset(data, *, for_freeze=False) -> None` raises ValueError; `python3 dataset.py validate INPUT`; `python3 dataset.py freeze INPUT --out NEW_PATH`.

- [x] 테스트를 먼저 쓰고 실행한다. 유효 번들은 validate 성공, 존재하지 않는 CLI는 실패해야 한다. 오류 계약 테스트는 구현 후 별도 실패→수정 사이클로 보완한다.
- [x] 참조·타입·모달리티 위치·출처 해시·AND/OR·qrels·분리 정책·검토 상태를 구현한다.
- [x] freeze는 동일 검증을 적용하고 status/frozen_at/payload_sha256을 기록한다. 해시는 해당 두 무결성 필드를 제외한 정규 JSON이며 검증 시 재확인한다. 출력은 exclusive create로 작성한다.
- [x] 전체 테스트와 합성 예제 validate/freeze/재validate를 실행한다. 기존 출력 재동결은 실패하고 기존 바이트가 유지되어야 한다.
- [x] 검증기·테스트·예제를 별도 커밋·push한다.

## Task 4: 배포 안내와 전체 확인

**Files:** `README.md`, `.github/workflows/test.yml`, `docs/validation.md`.

- [x] 설치·스킬 호출·예제 CLI 명령·검증의 한계를 README에 쓴다.
- [x] GitHub Actions에서 전체 unittest와 예제 검증을 실행하도록 설정한다.
- [x] 독립 전체 리뷰를 수행하고 중요한 결함은 재현 테스트 후 고친다.
- [x] 깨끗한 체크아웃에서 전체 테스트와 예제 동결을 실행한다.
- [x] 진행표·검증 기록을 갱신하고 커밋·push한다. GitHub 공개 상태·원격 HEAD 일치·CI·Orca 등록을 확인한다.
