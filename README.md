# rag-eval-dataset

**데이터와 사용 과업을 먼저 묻고, 원본 근거를 추적할 수 있는 RAG 평가 데이터셋을 만드는 에이전트 스킬입니다.**

문서·표·이미지·음성 등 낯선 입력의 처리 가능성을 먼저 판단합니다. 원본 없는 벡터처럼 정답을 검증할 수 없는 입력은 중단합니다.
모든 형식을 자동 파싱하는 앱이나 RAG 성능 측정기는 아닙니다. 에이전트가 분석·문항 생성·의미 검토를 수행하고, 포함된 CLI가 데이터 계약을 검사합니다.

## 사용

저장소를 복제한 후 `skills/rag-dataset-builder` 폴더를 사용하는 에이전트의 스킬 디렉터리에 복사합니다.
Codex 기본 경로는 `~/.codex/skills/`입니다. 같은 이름의 기존 스킬이 있으면 먼저 비교하고 덮어쓰지 않습니다.

```sh
git clone https://github.com/dtype2100/rag-eval-dataset.git
cd rag-eval-dataset
cp -R skills/rag-dataset-builder ~/.codex/skills/
```

새 세션에서 호출 예시:

> `$rag-dataset-builder`로 이 자료를 분석해서 RAG 평가 데이터셋을 만들어줘. 먼저 어떤 데이터와 사용 과업인지 질문해줘.

설치 없이 [SKILL.md](skills/rag-dataset-builder/SKILL.md)를 직접 읽도록 지시할 수도 있습니다.
실제 생성에는 읽을 수 있는 자료, 평가 목적, 실행 환경의 에이전트/도구가 필요합니다. CLI만 실행해서 문항이 자동 생성되지는 않습니다.

## 포함된 도구

Python 3.10+만 필요하며 런타임 패키지 설치는 없습니다.

```sh
python3 skills/rag-dataset-builder/scripts/dataset.py validate examples/toy/dataset.json
python3 skills/rag-dataset-builder/scripts/dataset.py freeze examples/toy/dataset.json --out /tmp/toy-dataset.v1.json
python3 skills/rag-dataset-builder/scripts/dataset.py validate /tmp/toy-dataset.v1.json
python3 -m unittest discover -s tests -v
```

freeze는 미확인 접수 정보·미검토 항목을 거절하며 기존 출력 파일을 덮어쓰지 않습니다.
예제는 두 개의 합성 정책 파일과 문항 3개입니다. 성능 벤치마크나 실사용 대표 표본으로 쓰지 마세요.
검토 정책과 독립 검토자의 실제 기록을 [계약](skills/rag-dataset-builder/references/contract.md)에 맞게 작성해야 합니다.

## 설계상 중요한 구분

| 구분 | 처리 |
|---|---|
| 검색만 / 답변까지 | 검색은 관련성 라벨, 답변에는 정답·루브릭·충분한 근거를 추가 |
| 원본 / 청크 | 정답은 원본의 안정된 근거 ID에 연결; 청크 변경은 매핑 변경 |
| 결합 / 대체 근거 | `[[A,B],[C]]`는 `(A AND B) OR C` |
| 미판정 / 오답 | 아직 판정하지 않은 자료를 자동으로 무관 처리하지 않음 |
| 검증기 통과 / 내용 검증 | 타입·참조·선언 검사는 자동화; 의미와 실제 독립성은 별도 검토 |

실제 코퍼스·질의·결과는 기본적으로 gitignore된 `data/`, `runs/` 아래에 저장합니다. 이 설정은 유출 방지 보증이 아니므로 공개 전 추적 파일을 직접 확인합니다.
기존 `rag-eval`의 청크 형식으로 손실되는 변환은 하지 않습니다. 자동 exporter·측정 어댑터·OCR 엔진은 포함하지 않습니다.

## 문서

- [계획·타당성 검토](docs/plan.md)
- [구현 계획](docs/implementation-plan.md)
- [독립 검토·행동 기준선](docs/review.md)
- [데이터 계약](skills/rag-dataset-builder/references/contract.md)
- [데이터별 분석 기준](skills/rag-dataset-builder/references/data-types.md)

이 스킬은 적용 범위 내 평가셋 구축을 돕습니다. 모든 입력에서 정답셋을 만들 수 있거나, 구조 검사를 통과한 정답이 참이라는 보장은 하지 않습니다.
