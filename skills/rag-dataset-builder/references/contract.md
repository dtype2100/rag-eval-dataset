# Dataset contract v1

`dataset.json`은 UTF-8 JSON 객체이며 `manifest`, `evidence`, `items`를 포함한다.
Python 3.10+ 표준 라이브러리 검증기는 이 계약의 구조·참조·동결 선언을 검사한다.
원본 추출·해시 대조·의미·실제 독립성은 생성/검토 담당자가 확인한다. 추가 메타데이터 필드는 허용한다.

## Manifest

| 필드 | 타입·규칙 |
|---|---|
| schema_version | 문자열 `1.0` |
| dataset_id, version, corpus_snapshot | 공백 아닌 문자열. corpus_snapshot은 평가 코퍼스의 불변 스냅샷 식별자 |
| status | `draft` 또는 `frozen` |
| task | `retrieval` 또는 `rag` |
| split_policy | `query-disjoint` 또는 `source-disjoint` |
| coverage, limitations | 공백 아닌 문자열의 배열. coverage는 동결 시 최소 1개; limitations는 빈 배열 허용하되 점검한 한계를 정직하게 보고 |
| intake | 아래 접수 필드 객체 |
| sources | 최소 1개의 출처 객체 |
| review | 검토 정책·승인 객체 |

intake의 문자열 필드: `data_description`, `user_task`, `query_language`, `scope`, `access_policy`, `external_processing`.
draft는 빈 문자열을 허용해 미확인을 표현한다. 다만 문항이 담긴 번들의 `data_description`, `user_task`는 항상 필요하다.
동결에는 모든 문자열을 채워야 한다. 허용 범위를 모르면 외부 전송하지 않고 확인한다.
`target_size`는 양의 정수다. 탈락으로 실제 수가 적으면 미달 사유를 limitations에 기록한다; 검증기는 수량을 자동 보충하지 않는다.

출처 객체 필드:

- `id`: 고유한 공백 아닌 문자열.
- `sha256`: 원본 파일/고정 직렬화 내보내기의 SHA-256 소문자 64자리. 검증기는 형식만 확인한다.
- `modality`: `text`, `table`, `image`, `audio`, `video`, `code`.
- `representation`: `native` 또는 `derived`.
- `transformation`: 비어 있지 않은 문자열. 파생본이면 OCR/전사/표 변환 등 사용한 방법·버전을 기록한다.
- `losses`: 공백 아닌 문자열 배열. 파생본은 배열을 필수로 기록하며 빈 배열은 알려진 손실이 없다는 검토자의 선언이다.
- `split_group`: 동일 원본/버전/중복·근접 중복 출처를 묶는 공백 아닌 문자열. group 결정의 완전성은 검토자가 확인한다.

review 필드: `policy`는 `independent` 또는 `human-required`.
동결 시 `approved_by`는 공백 아닌 문자열이고 `approved_at`은 타임존이 있는 ISO 8601 시각이다.
이 승인은 실제 수행한 데이터셋 검토 승인이다. 저장소 공개 승인과 혼동하지 않는다.

## Evidence

각 객체: `id`, `source_id`, `modality`, `locator`, `content`.
`id`는 고유한 문자열, source_id는 manifest.sources 참조, content는 검토에 사용한 원문 발췌/전사/설명이다.
content 문자열만으로 멀티모달 원본을 대체했다고 주장하지 않는다. locator의 좌표는 원본 또는 명시한 불변 추출물 기준이다.
modality는 출처와 같아야 하며, OCR된 이미지의 content가 텍스트여도 근거 modality는 image이다.

| modality | locator 필수 필드 |
|---|---|
| text | `path`: 문자열, `start`: 0 이상 정수, `end`: start보다 큰 정수. 문자열 offset은 Unicode code point 기준; PDF는 고정 추출 텍스트 경로와 page 메타데이터를 함께 보존 |
| table | `sheet`, `row`: 공백 아닌 문자열; `columns`: 공백 아닌 고유 문자열 1개 이상. row는 불변 행 키 또는 해당 스냅샷의 행 번호 문자열 |
| image | `page`: 1 이상 정수, `bbox`: [x0,y0,x1,y1], 0..1 정규화 좌표, x0<x1 및 y0<y1 |
| audio/video | `start_seconds`, `end_seconds`: 유한 숫자, 0<=start<end |
| code | `path`: 문자열, `start_line`, `end_line`: 1 이상 정수, start<=end |

문자열 경로·내용·URL은 식별 자료로만 처리한다. CLI는 해당 경로를 열거나 URL을 요청하거나 코드를 실행하지 않는다.
정확한 content-offset 일치나 bbox의 실제 대상 포함 여부는 원본 검토 항목이다.

## Items

| 필드 | 타입·규칙 |
|---|---|
| id | 문항 내 고유한 문자열 |
| query | 공백 아닌 문자열. 멀티모달 질의도 검색 지시 텍스트를 포함 |
| query_evidence_ids | 선택: 입력 이미지/음성 등 기존 evidence ID 배열. 입력 자산은 의도하지 않으면 후보 인덱스에서 제외하며 실행 어댑터에서 구분 |
| split | `dev` 또는 `test` |
| leakage_group | 같은 질문/패러프레이즈를 묶는 문자열 |
| query_type | 문자열: fact, multi-hop 등 실제 과업에 맞게 선택 |
| origin | `real` 또는 `synthetic` |
| author | 문항·라벨 작성자의 식별자. 실제 질의도 라벨 작성자를 기록 |
| expected_action | `retrieve`, `answer`, `abstain`, `clarify` |
| reference_answer | 문자열; 답변 문항은 비어 있으면 안 됨 |
| evidence_sets | 고유 근거 ID들의 비어 있지 않은 배열들을 담은 배열. 전체 빈 배열은 검색 전용/거절/되묻기에서 허용 |
| relevance_judgments | `{근거ID: 0 또는 1 또는 2}`. 0=무관, 1=부분 관련, 2=직접 관련. 미판정은 키 없음 |
| rubric | 공백 아닌 문자열의 배열. 답변/거절/되묻기에는 1개 이상 |
| rationale | 거절/되묻기 시 공백 아닌 문자열: 시점·권한·확인 범위와 기대 행동의 이유 |
| verification | 아래 검토 객체 |

`retrieve`는 task=retrieval에서만, `answer`는 task=rag에서만 사용한다.
retrieve는 양성 qrels가 1개 이상 필요하며 정답 답변·충분 근거는 없어도 된다.
answer는 정답 답변·루브릭·충분 근거 집합이 필요하다. 집합의 모든 근거는 양성 qrels로도 판정되어야 한다.
abstain/clarify는 충분한 답변 근거를 주장하지 않으므로 evidence_sets=[]이고 답변/관련성 필드는 빈 값도 허용한다.

`[[X,Y],[Z]]`는 `(X AND Y) OR Z`이다. 대체 출처가 X와 동등하면 해당 대체가 포함된 충분 근거 집합도 기록한다.
qrels는 관련성 라벨이며 이 논리 집합과 다르다. 하나라도 찾았다는 이유로 결합형 문항을 통과시키지 않는다.
미판정 결과는 전체 정답 목록이 완전하다고 가정해 오답 처리하지 않고 추가 판정 대상으로 보낸다.

verification 필드:

- `status`: `pending`, `accepted`, `rejected`.
- `reviewer`: 문자열. pending/rejected 상태는 빈 문자열 허용.
- `method`: `human`, `llm`, `hybrid` 중 하나.
- `independent`: boolean. accepted는 true이고 reviewer는 author와 달라야 한다.
- `notes`: 문자열. 원문 대조 결과·미해결 문제를 기록한다. accepted는 공백 아니어야 한다.

human-required 정책에서는 accepted 항목 method가 human/hybrid여야 한다.
검토자 이름이 다르다고 독립성을 입증한 것은 아니다. 실제 독립 컨텍스트/담당자 분리를 수행하고 기록한다.

## 분리·동결·연결

- 동일한 query 문자열(공백·대소문자 정규화) 또는 leakage_group이 dev/test 양쪽에 있으면 거절한다.
- source-disjoint는 양성 qrels 및 evidence_sets가 참조한 source.split_group도 dev/test 교차를 금지한다. query 자산은 후보 근거와 역할이 다르므로 이 검사에 포함하지 않는다.
- freeze는 모든 항목 accepted, 접수 필수 문자열, coverage, 검토 승인을 요구한다. 입력 자체가 frozen이면 같은 조건과 해시를 다시 검사한다.
- `frozen_at`은 UTC ISO 8601 시각. `payload_sha256`은 manifest에서 payload_sha256/frozen_at을 제외하고 전체 번들을 `json.dumps(ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)`한 UTF-8 바이트의 SHA-256이다. 봉인 값은 변경 탐지용이며 재계산 가능한 서명 없는 해시다.
- 기존 출력은 덮어쓰지 않는다. 동결 이후 변경은 version을 바꾸어 새 파일로 기록한다. CLI는 저장소 전체의 버전 중복을 탐지하지 않는다.
- 기존 rag-eval 0.1.0에 연결할 때 안정 근거→청크 매핑을 먼저 검증한다. AND/OR, 이미지 질의, 등급 qrels, 거절/되묻기 의미가 손실되는 변환은 수행하지 않는다. 이 버전에는 exporter나 측정 어댑터가 없다.

JSONL로 작업했다면 이 구조로 명시적으로 묶는다. 파일명만 바꿔 JSONL을 JSON으로 가장하지 않는다.
