/*
 * 앙개봇 Android Bridge v0.4.2 명령 파서 — 기존 기능 및 단축 명령 전체 상세 설명
 * 1. 기존 사용자가 설정한 '앙개야' 등의 호출어를 정확히 인식하고, 호출어 바로 뒤 명령·인수를 분리한다.
 * 2. 호출어 일부만 일치하는 텍스트는 무시하여 일반 카카오톡 대화에서 오작동하지 않는다.
 * 3. 호출어만 입력하면 기존 '도움말' 명령을 반환하고 기존 모든 장문 명령을 그대로 지원한다.
 * 4. 기존 '테스트/ping/상태/도움말/help' 로컬 응답과 안내 텍스트를 모두 유지한다.
 * 5. 계산/시간/서버상태 및 운영 명령, 주식 메모리7/그룹/분석, AI 질문/요약 등은 기존 Python Bridge 경로를 유지한다.
 * 6. 새 정확한 단축 호출 '주'를 Python '주식' 명령(인수 없음=기존 주식 도움말)에 대응한다.
 * 7. '주 분 삼성전자'를 '주식 분석 삼성전자'로 바꾸고 한글 종목·기존 티커·그룹명도 그대로 전달한다.
 * 8. '주 분'만 입력하면 지원되는 기존 '주식 도움말'을 반환해 분석 대상 입력 방법을 안내한다.
 * 9. '주 목록', '주 반도체', '주 미국시총10'처럼 다른 기존 주식 인수는 변형 없이 전달한다.
 * 10. '주식', '주변', '주분', 'ㅈㅅ'처럼 경계가 없는 문자열을 임의로 단축 호출 처리하지 않는다.
 * 11. 앱 설정의 호출어를 '주'로 변경한 사용자는 기존 호출어 방식이 우선되도록 해 동작을 보존한다.
 * 12. 알림 수신, 허용 방/발신자, 중복 검출, Android 관리 UI, SQLite 로그, 기존 답장/오류/AI OFF 처리는 변경하지 않는다.
 * 13. 단축 인식은 문자열 해석에만 적용하고 권한 우회·외부 URL·임의 코드 실행·자동 매매·가격 알림은 추가하지 않는다.
 * 18. v0.4.3 단축 '주'는 주식 메뉴를 열며 기존 '앙개야 주식' 도움말 동작은 변경하지 않는다.
 * 19. 번호 '1'~'9'의 수신 및 세션 범위 검사는 별도 MenuSelectionGate가 수행한다.
 * 20. 기존 '주 분 종목명', '주 목록', 사용자 호출어, 로그/AI/카톡 응답을 그대로 유지한다.
 * 21. v0.4.5는 배터리 표시를 별도 모듈에서 추가하므로 파싱 동작을 보존하고 로컬 상태·도움말의 버전만 갱신한다.
 * 22. v0.4.5는 최대 10종목 선택/배터리 상태를 지원하고 로컬 상태·도움말 버전만 갱신한다.
 * 23. 기존 긴 호출어/주·주 분·숫자 선택·AI OFF/명령 파싱·로그/권한·UI 동작은 모두 보존한다.
 * 24. 정확한 한 글자 앙/민/요/여/종/영을 통합 홈/콘텐츠 메뉴로 연결한다.
 * 25. 상/도는 Android 로컬 상태/도움말을 호출하며 주 단축 분석 기능을 유지한다.
 * 26. 앙개야 단독과 앙개야 메뉴는 홈으로 연결하고 기존 장문 명령은 유지한다.
 * 27. 일반 단어의 앞 한 글자를 단축어로 오인하지 않고 사용자 호출어를 우선한다.
 * 28. 날씨 단축 '날' 및 읽기 전용 설정·운영 단축 '설'을 추가하고 '영' 메뉴 호출을 종료한다.
 * 29. '앙패스(메뉴 점프)'는 '주 2', '주 2 2', '앙 1 2', '설 3'의 정확한 연속 숫자만 한 번에 Core로 전달한다.
 * 30. 주 분/주 목록/주 분석 등의 기존 별칭, 사용자 호출어, 5분 숫자 메뉴·보안·로그 동작을 그대로 보존한다.
 * 31. 최종 단계의 정상 API 응답 외에 중간 단계별 카톡 자동발신을 하지 않는다.
 * 32. 새 Android Bridge v0.4.9과 도움말을 표시하고 기타 로컬 명령/UI/설정·로그를 유지한다.
 * 33. v0.4.9는 상태·테스트·도움말 표시 버전만 갱신하고 기존 파서·메뉴·AI/로그·사용자 호출어는 유지한다.
 * 34. v0.4.10 사용자의 카카오톡 테스트/ping·계산·질문 명령을 무응답으로 비활성화한다.
 * 35. 도/앙개야 도움말은 설정 8번과 같은 간결한 목록을 제공하며 통합 상태는 설 1에서 조회한다.
 * 36. 그 외 기존 기능(주식/그룹/AI요약/배터리/로그/설정/RemoteInput/관리 UI)은 보존한다.
 * 37. v0.4.11 신규 부·투·메 단축 메뉴와 카톡 직접 부동산·투자·메모·일정·기록 명령을 지원한다.
 * 38. 메뉴 경로는 기존 정확한 번호 검증을 거치고 일반 문장 오인식·삭제된 테스트 명령·로그/권한 흐름을 보존한다.
 * 39. v0.4.12 홈 순서 변경에 맞춰 부·금·개 단축 메뉴와 번호 경로를 지원하되 기존 부·투·메 별칭도 유지한다.
 * 40. Android 로컬 '도' 도움말을 Core 설정 8과 동일하게 8줄로 정리하고 상태 버전을 갱신한다.
 * 41. 날 오늘/내일/주간 및 날 지역 <지명>을 Python 날씨 모듈로 전달하고 날 1~4 번호 점프는 보존한다.
 * 42. 기존 호출어/카톡 일반 대화 차단/권한·로그·메뉴·배터리 동작을 변경하지 않는다.
 * 43. 부 매매/시세/전세/월세/지역 단축 조회를 '실거래' Python 명령에 연결하고 부 메뉴·번호·개인 기록을 보존한다.
 * 44. 지정된 부동산 동사 외의 일반 문장은 기존대로 무시하고 별도 임의 명령을 실행하지 않는다.
 * 45. 기존 로컬 도움말은 8줄로 유지하면서 부 3~5 실거래 기능을 안내한다.
 * 46. 메모리7 직접 명령·반도체 개인그룹·주식 홈의 5개 시세에서는 99 상세 전환을 지원하고 주 1 99/주 2 99 등 안전한 번호 경로를 전달한다.
 * 47. 주식 메뉴를 8개로 재정렬하면서 사용자 그룹 9/10번째 분석·0 이전/00 홈·8줄 로컬 도움말·인증/로그를 유지한다.
 * 48. 주식 1~5 고정 시세의 1~19 분석/99 상세를 경로·활성 메뉴 입력에서 지원하고 구형 97/98 파싱·1~10/00 및 일상 숫자 채팅 거부를 보존한다.
 * 49. 주 1/2/3/4/5 시세에서 전체 19/10/13/19/5종목을 한 번에 표시하고 섹터에 한해 1~19 분석·99 상세를 허용하며 구형 97/98 인식은 유지한다.
 * 50. '앙개야 모듈'은 기존 접두어 인증을 사용하는 정확한 로컬 조회 명령으로, 다른 방의 답장 모듈이나 Python 토큰은 노출하지 않는다.
 * 51. 기존 도움말 8줄·주 분·1~10 다른 메뉴·AI OFF/로그/숫자 게이트는 보존한다.
 * 52. 주식홈 1 반도체주19·2 미국시총10·3 AI·4 반도체기자재·5 데센·6 최근·7 관심목록·8 분석 새 번호 체계를 8줄 로컬 도움말에 반영한다.
 * 53. 과거 메모리7/반도체 개인그룹의 직접 명령과 인증·로그·종목 번호·다른 섹터 단축명령은 유지한다.
 * 54. 이미지 테스트는 기존 일반 장문 파싱을 재사용하며 다른 단축어/텍스트 답장/로그를 보존한다.
 * 55. v0.4.15 표시만 갱신하고 미지원 명령의 기존 처리 흐름·도움말 8줄을 유지한다.
 * 56. v0.4.16 이미지 자동시험은 기존 장문 명령 파서에서 처리하며 로컬 상태 버전만 올린다.
 * 57. 기존 주식·날씨·부동산·메모·AI·숫자 선택/로그 및 8줄 도움말은 유지한다.
 * 58. 이미지 자동전송 v0.4.17의 상태 버전만 갱신하고 모든 기존 명령 인식은 보존한다.
 * 59. v0.4.18의 화면 깨우기 시도 버전만 갱신하고 모든 기존 명령/로그/UI를 유지한다.
 * 60. v0.4.19의 1명 사진 전송 버튼 인식 개선에 맞춰 상태 버전만 올리고 명령 파서 및 전체 도움말을 보존한다.
 * 61. v0.4.20에서 정확한 할/할일 단축 및 앙개야 할일 명령으로 개인 할 일 등록·완료·삭제를 Python Core에 전달한다.
 * 62. 기존 앙/주/개/메/부 등 단축어, 숫자 메뉴, 기존 개인정보 보호·로그·이미지 자동전송 기능을 보존한다.
 * 63. v0.4.21은 사용자 입력 '개 5 할일 추가 ...'를 명시적 개인 할 일 명령으로 정확히 인식한다.
 * 64. 개 5 숫자 경로, 일반 대화 차단, 기존 단축·알림/이미지/주식·로그/UI를 변경하지 않는다.
 * 65. v0.4.22에서 기존 장문 "앙개야 이미지 직공유진단/직공유시험"을 허용목록 기반 이미지 시험에 연결한다.
 * 66. 나머지 기존 단축/주식/개인/날씨 명령 파서는 절대 변경하지 않는다.
 * 67. v0.4.23의 앙개야 이미지 직공유경로확인도 기존 정확한 장문 호출어·허용목록을 그대로 사용한다.
 * 68. v0.4.24는 앙개야 이미지 직공유대조를 같은 정확한 호출어와 알림 인증 흐름으로 처리한다.
 */
package kr.co.angaebot.bridge

sealed interface ParseResult {
    data object NoTrigger : ParseResult
    data class Command(val name: String, val argument: String) : ParseResult
}

object CommandParser {
    // 사용자 요청으로 비활성화한 카카오톡 사용자 명령. Python 내부 API는 레거시 호환성을 위해 유지한다.
    private val retiredUserCommands = setOf("테스트", "ping", "계산", "질문")

    fun parse(text: String, wakeWord: String): ParseResult {
        val message = text.trim()
        val prefix = wakeWord.trim()
        if (prefix.isEmpty()) return ParseResult.NoTrigger
        // 호출어는 정확한 한 글자 또는 공백+숫자 경로로만 인식한다.
        // 접두사가 일반 문장에 우연히 등장하면 실행하지 않는다.
        val segments = message.split(Regex("\\s+"))
        val index = segments.firstOrNull().orEmpty()
        val numericPath = segments.size in 2..6 &&
            segments.drop(1).all { it.matches(Regex("(?:1[1-9]|97|98|99|00|10|[0-9])")) }
        if (message != prefix) {
            val root = when (index) {
                "앙" -> "홈"
                "민" -> "배드민턴"
                "요" -> "요리"
                "여" -> "여행"
                "종" -> "종친"
                "날" -> "날씨"
                "설" -> "설정"
                "부" -> "부동산"
                "금" -> "금융·투자"
                "개" -> "개인"
                "투" -> "금융·투자" // 기존 단축어 호환
                "메" -> "개인" // 기존 단축어 호환
                else -> null
            }
            if (root != null) {
                if (segments.size == 1) return ParseResult.Command("메뉴", root)
                // 개인 메뉴의 '개 5 할일 추가 제목'을 할 일 직접 명령으로 처리한다.
                // 기존 '개 5' 숫자 메뉴와 다른 메뉴 경로에는 전혀 영향을 주지 않는다.
                if (index == "개" && segments.size >= 3 && segments[1] == "5" &&
                    segments[2] == "할일") {
                    val taskArgument = segments.drop(3).joinToString(" ")
                    return ParseResult.Command("할일",
                        if (taskArgument.isBlank()) "목록" else taskArgument)
                }
                if (numericPath) {
                    return ParseResult.Command("메뉴", "경로 $root ${segments.drop(1).joinToString(" ")}")
                }
                if (index == "부") {
                    val action = segments.drop(1).joinToString(" ")
                    val verb = action.substringBefore(' ')
                    if (verb in setOf("시세", "매매", "전세", "월세", "지역", "실거래")) {
                        return ParseResult.Command("실거래", action)
                    }
                }
                if (index == "날") {
                    val action = segments.drop(1).joinToString(" ")
                    if (action in setOf("오늘", "내일", "주간", "지역") ||
                        (action.startsWith("지역 ") && action.length > 3)) {
                        return ParseResult.Command("날씨", action)
                    }
                }
                return ParseResult.NoTrigger
            }
            when (message) {
                "상" -> return ParseResult.Command("상태", "")
                "도" -> return ParseResult.Command("도움말", "")
            }
            // 개인 할 일은 독립 단축 명령. 일반 단어의 접두사와 우연히 일치하면 인식하지 않는다.
            if (index == "할" || index == "할일") {
                val todoArgument = message.substring(index.length).trim()
                return ParseResult.Command("할일", if (todoArgument.isEmpty()) "목록" else todoArgument)
            }
        }
        // '주'는 사용자가 직접 선택한 짧은 주식 호출어. 원래 호출어 및 사용자 설정을 먼저 보호한다.
        // 정확히 '주'이거나 '주'+공백/탭/개행일 때만 사용하고, 붙여 쓴 일반 단어는 무시한다.
        if (prefix != "주" && message.isNotEmpty() && message[0] == '주' &&
            (message.length == 1 || message[1].isWhitespace())) {
            val stockArgument = message.substring(1).trim()
            if (stockArgument.isEmpty()) return ParseResult.Command("주식", "메뉴")
            val parts = stockArgument.split(Regex("\\s+"))
            if (parts.size in 1..5 && parts.all { it.matches(Regex("(?:1[1-9]|97|98|99|00|10|[0-9])")) }) {
                return ParseResult.Command("메뉴", "경로 주식 ${parts.joinToString(" ")}")
            }
            val action = stockArgument.takeWhile { !it.isWhitespace() }
            if (action == "분") {
                val target = stockArgument.substring(action.length).trim()
                return ParseResult.Command("주식", if (target.isEmpty()) "도움말" else "분석 $target")
            }
            return ParseResult.Command("주식", stockArgument)
        }
        if (prefix.isEmpty() || !message.startsWith(prefix)) return ParseResult.NoTrigger
        val rest = message.substring(prefix.length)
        if (rest.isNotEmpty() && !rest.first().isWhitespace()) return ParseResult.NoTrigger
        val commandText = rest.trim()
        if (commandText.isBlank()) {
            return if (prefix == "앙개야") ParseResult.Command("메뉴", "홈")
                   else ParseResult.Command("도움말", "")
        }
        val command = commandText.substringBefore(' ').trim()
        if (command in retiredUserCommands) return ParseResult.NoTrigger
        val argument = commandText.substringAfter(' ', "").trim()
        if (command == "메뉴" && argument.isEmpty()) return ParseResult.Command("메뉴", "홈")
        if (command == "메뉴" && argument.split(Regex("\\s+")).let { parts ->
                parts.size in 1..5 && parts.all { it.matches(Regex("(?:1[1-9]|97|98|99|00|10|[0-9])")) }
            }) return ParseResult.Command("메뉴", "경로 홈 $argument")
        return ParseResult.Command(command, argument)
    }
}

object LocalCommandExecutor {
    fun execute(name: String, argument: String): String = when (name) {
        "상태" -> "✅ Android Bridge v0.4.24 · Galaxy S20+\n카카오톡 알림 응답 · Python 연결은 선택형\n서버·서비스·배포 통합 상태: 설 1"
        "도움말", "help" -> listOf(
            "📖 앙개봇 도움말",
            "앙(홈) · 주(주식) · 설(설정)",
            "부(부동산) · 금(금융·투자) · 개(개인 메모·일정)",
            "여(여행) · 민(배드민턴) · 요(요리) · 종(종친) · 날(날씨)",
            "설 1 통합 상태 · 설 7 전체 메뉴 · 설 8 도움말",
            "주 1 반도체주 · 2 미국시총10 · 3 AI · 4 반도체기자재 · 5 데센",
            "앙 2/3/9 메모·일정 · 개 5 할일 · 부 3~5 실거래 · 날 지역 서울",
            "주 6 최근 · 7 관심목록 · 8 분석 · 주 분 삼성전자 · 1~19 · 99 · 0/00 · 앙개야 모듈"
        ).joinToString("\n")
        else -> "지원하지 않는 명령: $name\n도움말: 앙개야 도움말"
    }
}
