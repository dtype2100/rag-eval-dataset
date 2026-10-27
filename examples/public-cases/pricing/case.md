# Cloudflare Workers 가격·한도 표 사례

권장 용도는 단위와 범위를 구분하는 공개 RAG 파일럿입니다. **실행 단계의 초안**이며, 독립 검토와 동결은 아직 하지 않았습니다.

## 자료와 과업

[Cloudflare Workers Pricing](https://developers.cloudflare.com/workers/platform/pricing/)과 [Limits](https://developers.cloudflare.com/workers/platform/limits/)의 production 커밋 `b58f85a4393a6074c50daf9f57c383d2a25f44a9`에서 선택한 사실을 사용합니다. 원본 수집 시각은 `2026-10-27T17:01:10.083286+00:00`입니다. 이후 바뀐 실시간 가격을 보장하지 않습니다.

한국어 사용자가 Free/Paid Standard의 가격과 HTTP 실행 한도를 조회하고, 월간 포함량·초과 요금·일일 한도·요청당 한도를 구분하는 과업입니다. `pricing.csv`는 원문에서 파생한 표이며, 원문의 표 전체를 복제한 파일이 아닙니다. 행 식별자는 `row_key`, 시트 식별자는 `pricing`입니다. `value`, `unit`, `period`, `allowance_kind`, `overage_usd`, `overage_quantity`, `overage_unit` 열이 포함량과 초과 요금의 단위를 분리합니다. 메모리는 원문처럼 MB로 유지하며 MiB로 바꾸지 않았습니다.

원본 2개와 파생 표 1개가 계약의 출처입니다. 원본 MDX·LICENSE·수집 기록은 Git에서 무시되는 `data/public-cases/pricing/`에만 있습니다. 공개 후보 근거는 표 10행과 명시된 원문 발췌 4개, 총 14개입니다. 원본 MDX의 모든 본문이나 가져온 `Render` 컴포넌트, 연결된 문서 전체를 평가 코퍼스로 주장하지 않습니다.

## 산출물과 검증

- `dataset.json`: 합성 한국어 문항 12개. 답변 10개, 제한 범위의 답변 거절 1개, 입력 부족으로 되묻기 1개입니다. 작성자는 모두 `case-pricing-author`이며 검토 상태는 모두 `pending`입니다.
- `pricing.csv`: 고정 행 키 10개를 가진 파생 표입니다. 근거의 `locator.sheet/row/columns`가 실제 셀을 가리키고 `locator.values`가 해당 문자열 셀 값을 보존합니다.
- `sources.json`: 공식 URL, 고정 raw URL, 커밋, 수집 시각, 라이선스, 원본/표 SHA-256, 행별 원문 오프셋과 변환 설명입니다.
- `round1.json`: 저자가 실제 실행한 구조·해시·셀·원문 위치·산술 검사 기록입니다. 46개 검사와 표 셀 100개가 통과했습니다. 의미 검증 승인이나 독립 검토 결과가 아닙니다.

문항은 단일 수치 조회, 포함량/초과 단가, HTTP 기본값/최대값 변환, 여러 근거의 결합, 기술적 무제한과 유료 초과분의 구별을 다룹니다. 계정당 최소 요금과 egress 면제는 서로 다른 근거가 모두 필요합니다. 계산 문항은 일반 동적 인바운드 요청 12,000,000건과 요청당 CPU 5ms를 가정합니다. Python `Decimal`로 확인한 값은 기본 USD 5.00 + 요청 초과 USD 0.60 + CPU 초과 USD 0.60 = 월 USD 6.20입니다. 세금·할인·다른 제품·캐시·정적 자산은 제외합니다.

저장소 루트에서 다음 명령으로 구조와 공개 원본/파생 근거의 일치를 다시 확인할 수 있습니다. `--fetch`는 명시된 고정 raw URL의 원본을 수집합니다.

```sh
python3 skills/rag-dataset-builder/scripts/dataset.py validate examples/public-cases/pricing/dataset.json
python3 scripts/verify_public_cases.py examples/public-cases/pricing/dataset.json --fetch
```

원본 수치의 변환과 계산의 저자 검사 스크립트는 현재 작업 환경의 무시 경로 `data/public-cases/pricing/check_case.py`에 남겼습니다. 공개 재검증기는 해시·셀·위치를 검사하며 정답의 의미나 실제 독립성을 보증하지 않습니다. 독립 담당자가 원문과 모든 문항을 검토한 후에만 `accepted`와 동결을 검토할 수 있습니다.

## 범위와 한계

가격 원문의 Cron/Queue 일반 최대값 설명과 한도 원문의 Cron 실행 간격별 설명은 범위가 다릅니다. 이번 사례는 이를 추측으로 합치지 않고 Cron/Queue 문항을 제외했습니다. 기타 Workers 제품, legacy 모델, 회사별 Enterprise 계약, 환율과 실제 계정 청구서는 다루지 않습니다. Enterprise 개별 단가의 부재는 이 고정 공개 범위에서 확인한 결과이며 모든 Cloudflare 자료의 부재를 증명하지 않습니다.

실제 고객 질의·운영 로그는 없고 전부 합성 문항입니다. 실제 RAG 실행, 검색 후보 풀, 생성 API 호출, 모델 성능 측정, 사람 검토와 판정자 일치도 연구는 수행하지 않았습니다. 공개된 설명용 test 사례이며 비공개 holdout 또는 source-disjoint 평가셋이 아닙니다. 미판정 검색 후보는 자동 오답 처리하지 않습니다.

## 출처 표시와 변경

Cloudflare, Inc. 및 기여자들의 문서를 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)에 따라 사용했습니다. 해당 커밋의 [저장소 LICENSE](https://github.com/cloudflare/cloudflare-docs/blob/b58f85a4393a6074c50daf9f57c383d2a25f44a9/LICENSE)와 [Pricing 원문](https://github.com/cloudflare/cloudflare-docs/blob/b58f85a4393a6074c50daf9f57c383d2a25f44a9/src/content/docs/workers/platform/pricing.mdx), [Limits 원문](https://github.com/cloudflare/cloudflare-docs/blob/b58f85a4393a6074c50daf9f57c383d2a25f44a9/src/content/docs/workers/platform/limits.mdx)을 보존한 링크로 확인할 수 있습니다. `case-pricing-author`가 필요한 사실을 선택하고 표 열·행 키를 새로 만들었으며, 백만 단위를 정수로 펼치고 초/분을 CPU 밀리초로 변환하고 한국어 합성 질의·정답을 작성했습니다. 원문의 링크·서식·대부분의 각주와 다른 제품 내용은 생략했습니다. Cloudflare의 후원이나 승인을 뜻하지 않습니다.
