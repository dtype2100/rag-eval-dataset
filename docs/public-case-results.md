# 공개 서비스 자료 3주제 × 3회 검증 결과

2026-10-28. **공개 공식 원문을 이용한 오프라인 평가셋 검증**을 완료했다.
실제 고객 질의 로그·운영 RAG·임베딩 모델 성능·사용자 효과는 측정하지 않았다.

## 결과

| 주제 | 실제 원문·파생 자료 | 문항/근거 | 1회 원문·구조 | 2회 독립 내용 검토 | 3회 오류 주입·동결 |
|---|---|---|---|---|---|
| [정책·FAQ](../examples/public-cases/policy/case.md) | GitHub Copilot 공식 원문 3개 | 12 / 15 | 해시·offset 통과 | 12개 승인 권고 | 5개 변조 거절, 동결·재검증 통과 |
| [요금·한도표](../examples/public-cases/pricing/case.md) | Cloudflare Workers 원문 2개 + 파생 CSV | 12 / 14 | 해시·표 100셀·산술 통과 | 12개 승인 권고, 질문 조건 명확화 확인 | 5개 변조 거절, 동결·재검증 통과 |
| [기술지원](../examples/public-cases/support/case.md) | Kubernetes 공식 원문 3개 | 12 / 14 | 해시·offset 통과 | 최초 11개 승인/1개 수정 → 수정 확인 후 12개 | 5개 변조 거절, 동결·재검증 통과 |

총 공식 원문 8개와 파생 표 1개, 합성 문항 36개, 근거 43개다.
문항은 답변 30개·범위 한정 거절 3개·되묻기 3개다. 실제 사용자 질문이라고 표시한 문항은 없다.
주제별 3회, 총 9개 검증 단위이며 동일 명령의 3회 반복으로 세지 않았다.

## 회차별로 다르게 확인한 것

1. **원문·구조:** 버전·라이선스·원본 SHA-256, 실제 문자 위치·줄·표 셀, 계약을 검사했다. 요금 산술은 별도 Decimal 연산으로 대조했다. 원문은 gitignore된 `data/public-cases/`에 보관하고 고정 raw URL로 재확보한다.
2. **독립 의미:** 다른 주제 작성자가 원문과 질문만 보고 `review-blind.json`에 먼저 답변을 저장한 뒤 생성 정답·기대 행동·근거 집합을 비교했다. 사람 검토가 아니라 별도 LLM 검토다. 수정 전 판정은 `round2.json`, 수정·해소 이력은 adjustments/addendum에 남겼다.
3. **오류 주입·동결:** 복사본의 원본 해시, 근거 위치/셀, 충분 근거 집합, dev/test 분리, 자기검토를 각각 깨뜨렸다. 주제별 5개, 총 15개가 의도한 이유로 거절됐다. 실제 입력과 원문을 변조하지 않았고 승인된 데이터셋은 새 파일로 동결했다.

기계 검증 결과의 `semantic_truth_verified=false`는 도구가 정답 의미를 자동 보증하지 않는다는 뜻이다. 독립 내용 검토 결과는 별도 기록으로 남긴다.

## 실제로 발견해 보완한 점

- **기술지원 rationale 부정어 오류:** `support-11`의 “결정할 수 있으므로”를 “결정할 수 없으므로”로 수정했다. 원인을 모르는 상태에서 되묻는 행동과 모순되던 문장이었다. 독립 검토자가 수정 후 일치를 확인했다.
- **요금 질문의 숨은 조건:** `pricing-05` 정답에만 있던 “일반 동적 요청” 조건을 질문에도 명시했다. 별도 검토자가 기존 근거·정답과 일치함을 확인했다.
- **검증기의 표 발췌 누락:** CSV 셀과 locator.values가 맞아도 evidence.content만 가짜 요금으로 바꾸면 통과하던 문제를 독립 코드 리뷰에서 재현했다. 회귀 실패를 확인한 뒤 열 순서대로 직렬화한 실제 셀과 content도 대조하도록 고쳤다.
- 스킬에는 정답뿐 아니라 rubric/rationale/expected_action의 모순 검사와 세 회차 주제 검증 절차를 반영했다.

자동 테스트는 기존 33개에서 43개로 늘었고, 표 content-only 변조도 거절하는 회귀를 포함해 모두 통과했다.

## 재현

`f17d9fa`의 깨끗한 Git 복제본에서 원문 8개를 새로 받아 세 사례의 15개 변조 거절과 동결본 원문 대조를 재현했다.
[GitHub CI 40548411481](https://github.com/dtype2100/rag-eval-dataset/actions/runs/40548411481)도 Python 3.10/3.13에서 전체 43개 테스트, 원문 다운로드·오류 주입·동결 왕복을 모두 통과했다.

로컬 macOS Python 3.14는 기본 CA 파일이 없어 첫 다운로드에서 인증서 검증 오류가 발생했다. 인증서 검증은 유지한 채 해당 검증 프로세스에 운영체제 신뢰 묶음 `SSL_CERT_FILE=/etc/ssl/cert.pem`을 지정해 재실행했고 통과했다. 시스템 설정이나 전역 인증서는 변경하지 않았다.
다른 환경에서도 인증서 오류가 나면 신뢰 가능한 CA 구성을 확인하며 TLS 검증을 끄지 않는다.

저장소 루트에서 실행한다. `--fetch`는 원문이 없을 때 허용된 공식 GitHub 저장소의 고정 커밋만 받는다. 파생 CSV는 저장소에 포함되어 있다.

```sh
python3 -m unittest discover -s tests -v
for topic in policy pricing support; do
  python3 scripts/verify_public_cases.py "examples/public-cases/$topic/dataset.json" --fetch --exercise
  python3 scripts/verify_public_cases.py "examples/public-cases/$topic/dataset.v1.json"
done
```

`dataset.json`은 검토된 draft, `dataset.v1.json`은 동결본이다. 동결본을 직접 편집하지 않는다.
범용 `dataset.py`는 선언·구조만 검사하며 원문 위치 검사까지 수행하지 않는다. 이 사례의 별도 auditor가 원문 해시·offset·CSV 셀·발췌 직렬화를 검사한다.
`--exercise`는 오염시킨 메모리 복사본만 검사하고 입력·원문 파일이나 검토 상태를 바꾸지 않는다.

## 한계와 후속 범위

표본은 주제당 12개로 작고 공개 합성 질문이므로 사용 빈도·난이도 분포를 대표한다고 볼 수 없다.
영문 정책, 한국어 요금/기술 질문을 다뤘지만 다국어 검색 성능을 측정한 것은 아니다.
GitHub Liquid와 Kubernetes shortcode는 고정 원문으로 대조했으며 웹 렌더링 전체를 재현하지 않았다. 문항은 읽을 수 있는 근거로 제한했다.
표 파생의 의미는 독립 LLM이 원문과 대조했다. 해시와 셀 일치만으로 변환의 의미적 정확성이 증명되지는 않는다.
이미지·음성·영상, 실제 사용자 로그, 사람 판정 일치도, 운영 서비스 경로·권한, 임베딩/검색·답변 품질, 사용자 효과는 후속 검증 대상이다.

공개 원문을 사용했으므로 **실서비스 로그 기반 검증** 또는 **운영 적용 효과 검증**으로 표현하지 않는다.

## 보고서 배포

[ChatGPT Sites 공개 보고서](https://rag-eval-dataset-report.datatype2100.chatgpt.site)에 이 세 주제와 검증 결과를 추가했다.
공개 접근 범위를 유지한 버전 2 배포의 `succeeded` 응답을 확인했다. Site 소스 커밋은 `dcff6150938d52fc0b02e5ee42fd1b2111b89207`이다.
이번 턴에는 연결된 브라우저가 없어 새 섹션의 실제 화면 QA는 재실행하지 못했다. 기존 모바일 화면 검증 기록과 구별한다. 배포 성공·소스 내용·논리 예제 테스트는 확인했다.

## 원문 출처

- [GitHub Copilot 플랜 관리](https://docs.github.com/en/copilot/how-tos/manage-your-account/view-and-change-your-copilot-plan), [라이선스 변경](https://docs.github.com/en/copilot/reference/copilot-billing/license-changes). 정확한 원문 3개·고정 커밋·라이선스는 policy/sources.json에 기록.
- [Cloudflare Workers 요금](https://developers.cloudflare.com/workers/platform/pricing/), [한도](https://developers.cloudflare.com/workers/platform/limits/). 원문 2개와 CSV 변환 출처는 pricing/sources.json에 기록.
- [Kubernetes Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/), [Debug Running Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/), [Images](https://kubernetes.io/docs/concepts/containers/images/). 원문·라이선스는 support/sources.json에 기록.
