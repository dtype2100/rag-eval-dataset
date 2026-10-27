# 최종 검증 계획과 결과

## 검증 범위와 성공 기준

| 대상 | 방법 | 성공 기준 | 결과 |
|---|---|---|---|
| 계약 검증기 | 전체 unittest | 모든 정상/오류/동결/누출 회귀 테스트 통과 | 로컬 33개 통과 |
| 스킬 형식 | skill-creator quick_validate | frontmatter·이름·완성 상태 통과 | 통과; 검사 도구만 격리된 PyYAML 사용, 프로젝트 런타임 의존성 없음 |
| 근거 연결 | 합성 원본 바이트 SHA-256, 문자 범위 대조 | 출처 2개·근거 3개 실제 값 일치 | 통과 |
| 의미 검토 | 작성과 분리된 LLM의 전체 원문 대조 | q1/q2 답변·AND/OR 대체 근거, q3 한정 코퍼스 거절 타당 | 3문항 accepted; 사람 검토/일치도 연구 미수행 |
| 동결 | freeze→validate, 출력 재사용, 변조 입력 | 왕복 검증 성공, 기존 파일 유지, 변조 거절 | 통과; 자동 회귀 테스트 포함 |
| 행동 검사 | 초기 3개 + 회차별 새 컨텍스트 1개 | 질문 선행·범위·독립 검토·오염·통계 과대해석 방지 | 6개 시나리오에서 요구 행동 관찰 |
| 독립 코드 리뷰 | 전체 스킬·계약·CLI·테스트 검토 | 중요한 결함 수정 | 큰 정수 예외·직렬화 경계 2건 수정; 회귀 테스트 통과 |
| 배포 재현 | 깨끗한 Git 복제본에서 전체 명령 | 테스트·예제 validate/freeze 재현 | `22d45fc` 복제본, Python 3.14.0에서 33개 테스트·예제 동결 왕복 및 논리 예제 8조합 통과 |
| 원격 CI | Python 3.10/3.13, 전체 테스트·예제 동결 | 두 버전 모두 성공 | [CI 40363708092](https://github.com/dtype2100/rag-eval-dataset/actions/runs/40363708092) 두 작업 모두 success |
| 공개 사이트 | 인터랙션 논리 검사, 화면 확인, 공개 배포 | 보고 내용 일치, AND/OR 8개 조합 통과, 공개 URL 발급 | 8조합 통과, Chrome 데스크톱·390px 모바일 화면 확인, 가로 넘침 없음, 공개 배포 succeeded |

최종 공개 보고서: [RAG Dataset Builder](https://rag-eval-dataset-report.datatype2100.chatgpt.site).
Sites 공개 접근(`access_mode=public`)과 배포 성공 응답을 확인했고, 실제 URL에서도 보고 내용과 예제 표시를 확인했다.
배포 버전 1의 Site 소스 커밋은 `2b68869e063f2fb9be7929bd76c520cb40608977`이며, GitHub의 `site/` 소스를 별도 Site 저장소로 동기화했다.
로컬 임시 서버는 검증 후 종료한다. 3회 개선 및 배포 검증 완료.

## 세 회차의 결과

1. 관련성 기준·판정 범위·무정답 확인 범위: 회귀 3개 추가, 전체 25개 통과.
2. 생성 이력·Unicode/동일 바이트 출처 누출: 회귀 3개 추가, 전체 28개 통과.
3. 검토 교정·불일치·불확실성 지침과 입력 경계: 회귀 5개 추가, 전체 33개 통과.

원인별 실패→수정→통과를 실행했다. 전체 테스트 수는 파라미터화된 세부 경우를 개별 테스트로 부풀리지 않은 unittest 메서드 개수다.
LLM 시나리오 수는 관찰 표본 수이며 성공률·보증 수준으로 환산하지 않는다.

## 독립 리뷰에 대한 결정

중요 지적 두 건은 모두 수용했다. 큰 정수는 부동소수로 변환하지 않고 범위를 검사하며, draft 검증에서도 확장 필드까지 유효 JSON/UTF-8 직렬화를 확인한다.
해시 재계산을 막는 서명, 원본 파일의 진위·정답 의미·실제 독립성 자동 증명, 파서·생성기·채점기·exporter는 범위에 추가하지 않았다.
이는 명시된 계약과 일치하며, 사용자가 이 기능까지 자동 보증된다고 이해하면 결과를 과신할 위험이 있어 README·스킬·보고서에 한계를 표시한다.
query 자산은 후보 정답 근거와 역할이 달라 source-disjoint의 양성 후보 교차 검사에서 제외한다. 입력 자산의 후보 인덱스 포함 여부는 과업 설계·실행 어댑터에서 관리한다.

## 미실행 범위

실제 고객 데이터, 운영 RAG, OCR/음성/영상 추출 엔진, 임베딩 모델별 성능 비교, 사람 판정 일치도, 디스크 장애 주입은 실행하지 않았다.
6가지 모달리티의 locator 형식을 검사했으며, 6가지 원본의 추출 품질이나 검색 성능을 검증했다는 뜻은 아니다.
서명 없는 체크섬은 우발적 변경 탐지용이다. 보안 서명이나 데이터 진실성 증명이 아니다.

## 재현 명령

```sh
python3 -m unittest discover -s tests -v
python3 skills/rag-dataset-builder/scripts/dataset.py validate examples/toy/dataset.json
python3 skills/rag-dataset-builder/scripts/dataset.py freeze examples/toy/dataset.json --out /tmp/unique-toy-version.json
python3 skills/rag-dataset-builder/scripts/dataset.py validate /tmp/unique-toy-version.json
```

이미 존재하는 출력 경로는 새 경로로 바꾼다. 실제 평가셋은 생성 실행별 코퍼스·검토 기준으로 다시 검증해야 한다.


## 2026-10-28 추가: 공개 서비스 자료 주제 검증

정책·요금표·기술지원 3주제를 각각 3회 검증했다. 공식 원문8개+파생표1개, 합성 질문36개·근거43개, 변조 통제15개 거절. 독립 검토에서 rationale 오류1개를 수정했고, 요금 질문1개를 명확히 했다. 표 content-only 변조 검사를 추가해 전체43개 자동 테스트가 통과했다. 상세 기록은 [public-case-results.md](public-case-results.md). 기존33개는 초기 구현 시점의 기록이다. 운영 RAG·고객 로그·임베딩 성능은 여전히 검증하지 않았다.
