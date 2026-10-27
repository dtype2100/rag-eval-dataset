# Kubernetes 기술 지원: 일반 문서와 실제 장애 진단의 경계

권장 용도는 공개 **개발용 초안**이다. 오류 토큰 검색뿐 아니라 추가 진단 정보가 필요한 상황도 함께 다루며, 현재 12문항 모두 독립 검토 전 `pending`이다.

## 과업과 원본

지원 담당자가 `CrashLoopBackOff`, `ImagePullBackOff`, `FailedScheduling`의 의미를 찾고, 이전 컨테이너 로그나 Pod 이벤트를 수집할 다음 명령을 고르는 과업이다. 일반 설명만으로 실제 환경의 장애 원인을 단정하는 응답도 구분한다.

평가 코퍼스는 [kubernetes/website](https://github.com/kubernetes/website)의 커밋 `ed70e311737a341574ed5758b7af24e3bba232cb`에 고정한 다음 영문 Markdown 3개다. 원본 다운로드 시각·SHA-256·고정 raw URL·저장 경로는 [sources.json](sources.json)에 있다.

| 출처 | 포함 범위 |
|---|---|
| [Pod Lifecycle](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/content/en/docs/concepts/workloads/pods/pod-lifecycle.md) | Pod phase와 컨테이너 state, crash loop, 원인 후보·진단 명령 |
| [Debug Running Pods](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/content/en/docs/tasks/debug/debug-application/debug-running-pod.md) | 현재·이전 컨테이너 로그, CPU 부족에 따른 FailedScheduling 문서 예제 |
| [Images](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/content/en/docs/concepts/containers/images.md) | ImagePullBackOff, imagePullSecrets 조건, 생성·업데이트 시 imagePullPolicy |

원본 전체는 저장소에서 무시하는 `data/public-cases/support/originals/`에 보존한다. 공개 번들은 필요한 연속 발췌 14개와 파생 질문·정답을 포함한다. 각 근거의 `locator.path`는 저장소 루트 상대 경로이며 `start/end`는 원본 UTF-8을 디코딩한 문자열의 Unicode code point 반개구간이다. 추가 `start_line/end_line`은 1부터 세는 실제 원본 행번호다. 링크 대상, 그림, Hugo shortcode와 외부 코드 예제는 펼치지 않았다.

## 문항 설계

한국어 합성 문항 12개 중 답변 10개, 되묻기 1개, 범위 내 답변 거절 1개다. 작성자 식별자는 모두 `case-support-author`다. 실제 고객 질의나 운영 로그는 사용하지 않았다. 오류 토큰을 붙인 진단 입력은 **합성 입력**으로, 발췌한 FailedScheduling 출력은 **공식 문서 예제**로 명시했다. 문서의 숫자나 이름을 실제 회사 장애의 기록으로 취급하지 않는다.

`support-01`, `04`, `05`, `08`, `09`는 두 근거를 함께 요구한다. `evidence_sets`의 한 집합 안에서는 AND이며 한 근거만 회수해서 충분한 답변으로 처리하면 안 된다. 선택한 직접·부분 관련·혼동 근거의 qrels를 기록했으며 미기재 근거는 미판정이다. 실제 검색 후보 풀이나 모든 청크의 전수 관련성 판정은 수행하지 않았다.

`support-11`은 상태 토큰만으로 원인·수정값을 결정할 수 없어 Pod/컨테이너 식별과 이벤트·로그를 요청한다. `support-12`는 일반 문서로 특정 회사의 배포 커밋·실제 재시작 횟수를 알 수 없는 상황이다. 답변 가능성 검토는 세 파일의 주제·선택 구간 대조 및 전체 파일의 사건 식별 문자열 검색이라는 `bounded` 범위다. 의미적 전수 부재를 증명한 것은 아니다.

관련 문항은 같은 `leakage_group`으로 묶었고 모두 `dev`에 둔다. 이 공개 예제는 비공개 최종 holdout이나 사전학습 오염이 없는 평가셋이 아니다.

## 1차 확인과 다음 검증

[round1.json](round1.json)은 실제 실행한 구조 검증 결과와 3개 원본 해시, 14개 발췌의 오프셋·행번호 대조 결과를 기록한다. 구조 검증은 다음 명령으로 재실행한다.

```sh
python3 skills/rag-dataset-builder/scripts/dataset.py validate examples/public-cases/support/dataset.json
```

원본 파일은 `sources.json`의 고정 `raw_url`에서 `path` 위치로 복원한 뒤 SHA-256을 대조한다. 이어 `text[start:end] == content`와 행번호를 비교한다. CLI 자체는 원본을 열거나 해시·오프셋의 실제 일치를 확인하지 않는다.

수행한 검증은 작성자의 기계적 대조다. 다음 검증은 작성자와 분리된 검토자가 원본을 읽고 정답·대체 근거·0/1/2 경계·되묻기/거절의 범위를 대조하는 것이다. 교정·불일치 해결과 실제 승인이 끝나기 전에는 동결하지 않는다. 실제 RAG 실행, 임베딩 비교, 응답 품질 점수나 사용자 영향은 측정하지 않았다.

## 출처와 변환 표시

원본: **Kubernetes Authors and kubernetes/website contributors**, 위의 세 문서, 고정 커밋 및 다운로드 시각은 `sources.json` 참조. 원본 저장소의 [LICENSE](https://github.com/kubernetes/website/blob/ed70e311737a341574ed5758b7af24e3bba232cb/LICENSE)는 [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)이다.

변경: 필요한 연속 구간을 원문 그대로 발췌하고 한국어 합성 질문·정답·루브릭·메타데이터를 추가했다. 이 지원 사례의 발췌 및 파생 콘텐츠에도 CC BY 4.0을 적용한다. Kubernetes 프로젝트가 이 사례를 승인하거나 보증했다는 뜻은 아니다. 조사 중 받은 `debug-pods.md`와 `README.md`는 평가 코퍼스에 넣지 않았으며 `LICENSE`는 라이선스 증빙으로만 보존했다.


## 후속 검증 완료

작성 직후 pending 기록은 round1.json의 이력이다. 독립 source-first 검토(round2.json 및 수정 addendum)를 거쳐 승인했고, round3.json에 5개 오류 주입 거절·동결·원문 재검증 결과를 기록했다. 최종본은 dataset.v1.json이며 실제 고객 로그/운영 RAG/임베딩 모델 검증은 아니다.
