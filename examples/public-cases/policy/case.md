# GitHub Copilot 구독·취소·지원 정책 공개 사례

권장 용도는 **공식 문서에 근거한 RAG 평가 계약과 근거 추적의 초안 사례 검토**다. 실제 고객 상담 품질이나 운영 중인 서비스의 성능을 증명하는 자료는 아니다.

## 접수와 사용 과업

부모 에이전트가 승인한 사례 목적은 공개된 GitHub 공식 문서에서 구독 취소·과금/접근 종료 시점·무료/조직 접근 예외·잠긴 계정의 지원 경로를 찾는 합성 RAG 평가셋을 만드는 것이다. 원자료는 영어 GitHub Docs Markdown 3개이며 실제 고객 문의나 로그는 사용하지 않았다. 사용자는 정책 조건에 맞는 답을 받고, 접근 방식이 빠진 질문에는 되묻고, 문서에 없는 보장 시간에는 답변을 유보하는 상황을 가정한다.

질문 생성 전에 확인된 범위는 이 접수 설명과 부모의 작업 지시다. 별도 실제 고객 업무 대표성이나 서비스 측정 승인을 추정하지 않는다. 외부 처리는 공개 페이지 열람·다운로드와 이 에이전트의 문항 작성으로 한정했다. 인증 API, 계정·구독 변경, 커밋·푸시는 수행하지 않았다.

## 원자료와 출처

모든 원문은 GitHub, Inc. 및 기여자의 공식 [github/docs 저장소](https://github.com/github/docs)의 커밋 `2853a7b4a1bd4e17da2a43cf2c8d7306d7d4a431`에 고정했다. 완전한 원문은 Git 추적에서 제외되는 `data/public-cases/policy/`에만 저장했다. [sources.json](sources.json)은 다운로드 URL, 공식 페이지 URL, SHA-256, 내려받은 시각, 경로, 라이선스와 저작자 표시를 독립적으로 담는다. 재현 시 그 파일의 `raw_url`을 해당 `path`에 저장한 뒤 해시를 확인하면 된다.

| 원문 ID | 자료 | 로컬 원문 |
|---|---|---|
| copilot-plan | [Viewing and changing your GitHub Copilot plan](https://docs.github.com/en/copilot/how-tos/manage-your-account/view-and-change-your-copilot-plan) | `data/public-cases/policy/view-and-change-your-copilot-plan.md` |
| copilot-license | [Making changes to your GitHub Copilot license](https://docs.github.com/en/copilot/reference/copilot-billing/license-changes) | `data/public-cases/policy/license-changes.md` |
| copilot-free-exception | [무료 접근 취소 예외 reusable](https://github.com/github/docs/blob/2853a7b4a1bd4e17da2a43cf2c8d7306d7d4a431/data/reusables/copilot/free-access-cancellation-note.md) | `data/public-cases/policy/free-access-cancellation-note.md` |

고정 커밋의 README는 `assets/`, `content/`, `data/` 내 문서·콘텐츠에 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)을 적용한다고 명시한다. 세 원문은 `content/`와 `data/`에 위치한다. 라이선스 전문과 README도 ignored 폴더에 보존했지만 평가 코퍼스에는 포함하지 않았다. 데이터셋에는 짧은 원문 발췌와 출처·저작자·라이선스를 남겼으며 질문과 정답은 합성·의역한 파생 작성물이다. GitHub의 후원이나 승인을 주장하지 않는다.

## 지원 범위와 구성

12개 문항은 전부 `origin=synthetic`, 작성자는 `case-policy-author`다. 답변 10개, 답변 유보 1개, 되묻기 1개이며 영어 질문·정답과 한국어 사례 설명을 제공한다. 개인 취소 효과가 겹치는 문항 q01/q03/q10은 같은 `leakage_group`으로 test에 함께 묶었다. dev 2개는 개인 업그레이드와 조직 좌석 추가, test 10개는 나머지다. 이는 공개 개발 사례이며 비공개 최종 holdout이 아니다.

개인 취소 후 현 기능 유지/Free 전환과 미사용 기간 환불 없음은 서로 다른 두 출처를 결합하는 문항(q10)으로 남겼다. 조직 좌석 해제와 취소(revocation)의 즉시 접근 상실 예외도 구별한다. q11은 세 저장 원문 안에서 지원 해결 시간 보장이 발견되지 않았다는 **bounded** 유보이며 전체 GitHub 지원 문서에 그런 보장이 없다는 주장이 아니다. q12는 개인 결제·검증된 무료 접근·조직/기업 제공 여부가 빠져 정책상 답이 달라지므로 되묻는다.

15개 근거의 `locator.start/end`는 저장된 전체 Markdown의 Unicode code point 기준 0부터 시작하는 끝 미포함 구간이다. `content`는 그 구간의 원문과 정확히 일치한다. 원문 Liquid 변수와 transclusion은 변형하지 않았다. Copilot/Free/GitHub Support의 표시명은 공식 렌더링 페이지와 대조했지만 일반 템플릿 렌더러를 실행한 것은 아니다. 다른 reusable 본문, 링크를 따라간 문서, 정확한 UI 메뉴 절차, 조직 좌석 배정에 따른 개인 플랜 자동 취소는 평가 범위에서 제외한다.

qrels는 질문별로 작성자가 골라 판정한 근거의 초안이다. 검색 후보 풀링이나 전체 청크 전수 판정은 수행하지 않았으며 미판정 결과를 자동으로 0점 처리하면 안 된다. 새로운 관련 근거를 찾으면 추가 판정해야 한다.

## 검증과 남은 검토

`round1.json`에 기존 계약 검증기 명령, 원문/라이선스 해시 대조, 모든 근거의 offset 일치 및 작성·검토 상태 확인 결과를 기록한다. 이 기계 검사는 의미상 정답, 질문 자연스러움, 대체 근거의 완전성이나 독립 검토를 대신하지 않는다.

모든 항목은 `verification.status=pending`이고 manifest 검토 승인도 비어 있다. 작성자의 자기 검토를 독립 승인으로 기록하지 않았다. 독립 검토자는 원문을 직접 읽고 정답·관련성·조건/예외·유보 범위·되묻기의 필요성·그룹 분리를 확인한 뒤 수정/승인해야 한다. 아직 동결하지 않았고 검색 시스템 측정·실고객 검증·통계적 성능 비교는 수행하지 않았다.


## 후속 검증 완료

작성 직후 pending 기록은 round1.json의 이력이다. 독립 source-first 검토(round2.json 및 수정 addendum)를 거쳐 승인했고, round3.json에 5개 오류 주입 거절·동결·원문 재검증 결과를 기록했다. 최종본은 dataset.v1.json이며 실제 고객 로그/운영 RAG/임베딩 모델 검증은 아니다.
