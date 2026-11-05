/*
 * 앙개봇 Android Bridge v0.4.9 응답 모듈 식별자와 배포정보 — 전체 기능
 * 1. 모든 카카오톡 자동응답의 본문 아래, 기존 배터리 상태 바로 위에 담당 모듈명·소스 경로를 표시한다.
 * 2. 기존 수신·RemoteInput·허용목록·명령·SQLite/안드로이드 로그·사용자 설정/UI/배터리를 보존한다.
 * 3. Python Core 응답은 사전에 정의된 짧은 module_source ID만 사용한다.
 * 4. Android 로컬 테스트/상태/도움말은 CommandParser.kt 소스로 표시한다.
 * 5. Python Core 연결 실패·OFF 상태는 PythonBridgeClient.kt로 표시한다.
 * 6. 배포 브랜치·커밋은 Core의 인증된 실제 로컬 배포 기록만 사용한다.
 * 7. 미기록/네트워크 오류 시 추측하지 않고 미확인으로 표시하며 GitHub main으로 오인하지 않는다.
 * 8. 허용된 저장소 파일 외의 임의 경로·토큰/로그 원문을 출력하지 않는다.
 * 9. 포맷터는 Android SDK 없이 테스트 가능한 순수 Kotlin 코드다.
 * 10. 이 파일은 네트워크/DB/설정 변경 및 카카오톡 전송 요청을 실행하지 않는다.
 * 11. v0.4.11 신규 개인 기록·부동산·금융 투자·일정 모듈의 실제 경로를 표기한다.
 */
package kr.co.angaebot.bridge

object ModuleSourceFormatter {
    private val sources = mapOf(
        "bridge.commands" to ("Bridge 명령·상태" to "app/src/main/java/kr/co/angaebot/bridge/CommandParser.kt"),
        "bridge.python" to ("Python 연결" to "app/src/main/java/kr/co/angaebot/bridge/PythonBridgeClient.kt"),
        "core.menu" to ("공통 메뉴" to "core/app/selection_menu.py"),
        "core.records" to ("개인 메모·일정" to "core/app/personal_records.py"),
        "core.market" to ("주식 시세" to "core/app/market.py"),
        "core.watchlists" to ("관심종목·그룹" to "core/app/watchlists.py"),
        "core.history" to ("주식 분석" to "core/app/history.py"),
        "core.ops" to ("서버·배포·로그" to "core/app/ops.py"),
        "core.ai" to ("AI 질의·요약" to "core/app/ai_engine.py"),
        "core.commands" to ("계산·시간·서버" to "core/app/commands.py"),
        "core.main" to ("Core 명령 분기" to "core/app/main.py")
    )

    fun append(reply: String, sourceId: String): String {
        val (name, path) = sources[sourceId] ?: sources.getValue("bridge.python")
        return reply.trimEnd('\n') + "\n🧩 기능 모듈: $name\n📂 $path"
    }

    fun localCommandSource(name: String): String =
        if (name in setOf("테스트", "ping", "상태", "도움말", "help")) "bridge.commands"
        else "bridge.python"

    fun statusDeployment(outcome: PythonOutcome?, coreEnabled: Boolean): String {
        if (!coreEnabled) return "📦 배포 정보: Python 연결 OFF · 브랜치 미확인"
        if (outcome !is PythonOutcome.Success || !outcome.commandOk) {
            return "📦 배포 정보: Core 확인 불가 · 브랜치 미확인"
        }
        val branch = outcome.deploymentBranch.ifBlank { "미기록 (확인 불가)" }
        val sha = outcome.deploymentSha.takeIf { it.length == 40 }?.take(12) ?: "미기록"
        return "📦 Core 배포 정보\n" + outcome.reply + "\n브랜치: " + branch + "\n커밋: " + sha
    }
}
