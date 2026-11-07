# MediaSender 기반 앙개봇 카카오톡 직접 공유 실험

## 2026-11-07 실기기 로그 판정과 A/B 대조 (Android v0.4.24)

- S20+ 21:08:54 `MEDIA_DIRECT_PROBE_STARTED`, `MEDIA_DIRECT_INTENT_STARTED`가 확인되고, 21:08:55/58 및 21:09:04 `MEDIA_DIRECT_PROBE_WAIT`, 21:09:14 `MEDIA_DIRECT_PROBE_TIMEOUT`이 확인됐다.
- `pickerHeading=true targetNameVisible=true roomChoices=0 sendButtons=0 autoClick=false`는 공유 화면 요소를 완전히 분류하지 못했다는 뜻이다. **타임아웃을 사진 전송 실패로 해석하지 않는다.** 사용자 화면에는 같은 분에 사진 말풍선이 나타났으나 이번 명령으로 새로 발송된 사진인지 아직 별도 증명이 필요하다.
- A/B 실험은 기존과 같은 테스트 PNG를 재사용하는 오류를 없앤다. 실제 발송 원인을 수신 사진 내부의 A/B 표식으로 구분한다.

**A — 직접 공유 힌트 포함:**
1. S20+ MediaSender 실험 스위치와 기존 이미지 자동 스위치 ON, 1:1 테스트 방 허용목록 확인.
2. S25에서 `앙개야 이미지 직공유진단` → 5분 내 `앙개야 이미지 직공유경로확인` 순서.
3. 앱은 A 전용 PNG(`A: DIRECT (KEY_ID)`)와 `key_id`, `key_type`, `key_from_direct_share`를 카카오톡 공유 Intent에 넣는다. 방 선택/보내기 버튼을 **자동 클릭하지 않는다.**
4. S25의 같은 방에 **A 문구가 새겨진 사진**이 새로 도착하는지 확인. 뜬 카카오톡 화면은 수동으로 전송 버튼을 누르지 말고 관찰한 후 닫는다.

**B — 직접 공유 힌트 제외:**
1. A 시험 화면을 닫고 다시 `앙개야 이미지 직공유진단`을 보낸다. 승인 토큰은 매번 1회 사용 후 폐기되므로 반드시 재진단한다.
2. 5분 이내 `앙개야 이미지 직공유대조` 입력.
3. 앱은 B 전용 PNG(`B: CONTROL (NO KEY_ID)`)를 만들고 A와 동일한 Intent 형식·플래그·관찰 모드로 공유하되 **채팅방 직접 지정 extra 3개를 넣지 않는다**.
4. 자동 버튼 클릭은 없지만 카카오톡 자체의 발송을 막지 않으므로, S25에 B 사진이 새로 도착했는지 반드시 확인한다.

**판정**: A만 수신되고 B는 수신되지 않으면 `key_id` 등 힌트의 효과를 지지한다. A와 B가 모두 수신되면 ID 없이도 가능한 다른 전송 경로이므로 직접 지정 효과를 확정하지 않는다. 둘 다 수신되지 않으면 미확인. 수신 여부뿐 아니라 `MEDIA_DIRECT_PROBE_STARTED`, `MEDIA_DIRECT_INTENT_STARTED`(A), `MEDIA_DIRECT_CONTROL_INTENT_STARTED`(B), `MEDIA_DIRECT_PROBE_RESULT`/TIMEOUT, `IMAGE_UI_ROOM_SELECTED`, `IMAGE_UI_SEND_REQUESTED` 등의 로그도 함께 확인한다.

**주의**: 이 실험은 공식 메시지 API가 아니며 카카오톡 내부 공유 동작을 활용한다. 앱 자체 자동 클릭은 차단하지만, Android Intent를 받은 카카오톡이 자동 발송하는 경우까지 막지는 못한다. 반드시 본인과의 1:1 시험 방에서만 진행하며 PIN 인증 잠금 정책은 기존 그대로 유지한다. **본인과의 실기기 결과가 확정되기 전에는 다른 대화방에 사용하지 않는다.**


## 목적
- 공개 소스 https://github.com/hehee9/mediaSender 의 Android 공유 Intent 설계에서 직접 채팅방 선택 아이디어만 참고한다.
- 별도 메신저봇R 설치 없이 앙개봇 Android Bridge 안에서 채팅방 ID 후보를 진단한다.
- MediaSender 원본 JavaScript는 복제하지 않는다. 참고한 세 Intent extra는 key_id, key_type, key_from_direct_share이다.
- 해당 값은 공식 카카오 메시지 API가 아니고 내부 공유 형식에 종속적이므로 카카오톡 업데이트에 따라 바뀔 수 있다.

## S20+ 안전 시험 절차
1. 기존 앙개봇 1:1 카카오톡 및 호출어·방/발신자 허용목록이 정상인지 확인한다. `앙개야 이미지 자동시험`이 작동하는 기존 경로는 그대로 유지한다.
2. S25에서 `앙개야 이미지 직공유진단` 전송. S20+는 알림 tag가 숫자 8~18자리인지, room과 sender가 정확히 같은지 검사한다. 성공 시 자릿수 및 끝 네 자리만 응답하고 5분짜리 일회성 메모리 승인을 남긴다. **진단 단계에서는 어떤 파일도 전송하지 않는다.**
3. S20+ Android Bridge의 ②-B-1 MediaSender 직공유 실험 스위치를 ON으로 하고 저장한다. 기존 ②-B 이미지 자동전송 스위치 및 접근성 서비스도 ON이어야 한다.
4. **권장 2차 검증**: 5분 내 S25에서 `앙개야 이미지 직공유경로확인`을 전송한다. 이 명령은 MediaSender의 direct-share 힌트로 카카오 공유 화면을 열지만 **수신 방 선택이나 보내기 버튼을 자동 클릭하지 않는다.** S20+에서 어떤 화면이 보이는지 직접 확인하고 건드리지 않는다. Android에서 다른 앱의 공유 처리 자체가 자동으로 진행되는 경우까지 강제로 금지하지는 못한다.
5. 로그 `MEDIA_DIRECT_PROBE_RESULT`의 `route=RECIPIENT_PICKER`라면 수신자 선택창이 표시되어 직접 지정 효과가 확인되지 않은 것. `TARGET_SCREEN_CANDIDATE`는 대상 텍스트/버튼이 함께 보이는 후보일 뿐 정확한 ID 또는 실제 발송 성공을 증명하지 않는다. `MEDIA_DIRECT_PROBE_WAIT`·`MEDIA_DIRECT_PROBE_TIMEOUT`이면 판단 보류. 화면에서는 자동 클릭 없이 20초까지 관찰한다.
6. 이전 실험의 `앙개야 이미지 직공유시험`은 기존 접근성 자동화의 방 선택·보내기 클릭을 **그대로 사용**한다. 사진이 도착해도 직접 채팅방 ID 동작을 입증하지 못한다. `MEDIA_DIRECT_FALLBACK_ROOM_CLICK` / `IMAGE_UI_ROOM_SELECTED`이 있으면 기존 방식으로 채팅방을 선택한 것.
7. 관찰용 화면을 닫은 후 반드시 새로운 `앙개야 이미지 직공유진단`을 먼저 보내야 한다. 진단 승인은 1회용이며 소모되면 재사용할 수 없다. 기존 사진 자동전송을 비교하려면 `앙개야 이미지 자동시험`을 사용한다. 부작용이 있으면 실험 스위치를 OFF 한다.
8. 이벤트 로그 `MEDIA_DIRECT_CANDIDATE`, `MEDIA_DIRECT_PROBE_QUEUED`, `MEDIA_DIRECT_INTENT_STARTED`, `MEDIA_DIRECT_PROBE_RESULT` 또는 `MEDIA_DIRECT_PROBE_TIMEOUT`을 확인한다. Intent 시작 성공은 실제 수신 확인이 아니다.

## 한계·안전
- Android StatusBarNotification.tag는 **알림 태그**일 뿐 실제 카카오톡 채팅방 ID인지 보증되지 않는다. 숫자가 보인다는 사실만으로는 직접 발송 성공 또는 올바른 대상 인증을 뜻하지 않는다.
- PIN·패턴·비밀번호 인증 잠금은 기존과 같이 거부한다. 화면 잠금 우회/비밀번호 입력 기능은 없다.
- 채팅방 표시 이름==발신자 표시 이름일 때만 개인 1:1 시험 후보로 처리한다. 단톡방 및 표시 이름 불일치 방에서는 거부한다. 이름만으로 계정 신원을 강하게 보증할 수는 없다.
- 별도 스위치 OFF가 초기값이고 기존 접근성 이미지 자동전송·텍스트 빠른답장 경로를 대체하지 않는다. 위험을 고려하여 의도한 테스트용 계정·방에서만 실행한다.
- 실험에는 내부 생성 PNG만 사용한다. 동영상/외부 URL/다중 파일은 이번 첫 단계에 도입하지 않고 채팅방 지정 자체를 검증한 다음 추가한다.
- 테스트 또는 직접 공유 요청이 오류 없이 반환됐다는 사실은 카카오톡 서버 업로드 완료나 상대방 수신의 증거가 아니다.
- 기존 DB, SQLite 로그, Python Core, 배터리 응답, Android Bridge 설정·UI, .env와 채팅 내용은 삭제하거나 초기화하지 않는다.
