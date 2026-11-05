/*
 * 앙개봇 v0.4.9 모듈 표시/브랜치 포맷터 회귀 테스트 — 전체 설명
 * 1. Android 로컬 상태·도움말을 기존 CommandParser.kt로 정확히 표기한다.
 * 2. Python 메뉴/시세/분석/운영 기능을 실제 소스 파일 경로에 연결한다.
 * 3. 응답 본문은 보존하고 담당 모듈명·경로만 추가함을 검증한다.
 * 4. 배포 브랜치/커밋은 Core 인증 응답에서만 읽으며 누락/연결 OFF는 미확인 표시한다.
 * 5. 모르는 모듈 ID는 Python 연결의 기본 경로로 안전하게 처리한다.
 * 6. 기존 배터리 푸터는 마지막 줄에 그대로 남고 SQLite/UI/RemoteInput을 수정하지 않는다.
 * 7. Android 기기/네트워크 없이 순수 Kotlin 테스트를 수행한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ModuleSourceFormatterTest {
    @Test fun allKnownSources() {
        assertTrue(ModuleSourceFormatter.append("시세", "core.market").contains("core/app/market.py"))
        assertTrue(ModuleSourceFormatter.append("분석", "core.history").contains("core/app/history.py"))
        assertTrue(ModuleSourceFormatter.append("설정", "core.ops").contains("core/app/ops.py"))
        assertTrue(ModuleSourceFormatter.append("홈", "core.menu").contains("core/app/selection_menu.py"))
        assertEquals("bridge.commands", ModuleSourceFormatter.localCommandSource("상태"))
        assertTrue(ModuleSourceFormatter.append("상태", "bridge.commands").contains("CommandParser.kt"))
    }
    @Test fun originalBodyAndBatteryCompatible() {
        val original = "✅ 앙개봇 상태"
        val body = ModuleSourceFormatter.append(original, "core.ops")
        assertTrue(body.startsWith(original))
        assertTrue(body.endsWith("core/app/ops.py"))
        val completed = BatteryStatusFormatter.append(body, 100, 100, BatteryChargeState.FULL)
        assertTrue(completed.indexOf("기능 모듈:") < completed.lastIndexOf("🔋"))
        assertTrue(completed.endsWith("🔋 S20+ 배터리 100% · 충전 완료"))
    }
    @Test fun branchFromCoreOnlyNoGuessing() {
        val verified = PythonOutcome.Success("🐍 Python 연결 정상 (v0.6.1)", false, true,
            deploymentBranch="feature/global-shortcut-menus-20261106",
            deploymentSha="0123456789abcdef0123456789abcdef01234567")
        val msg=ModuleSourceFormatter.statusDeployment(verified,true)
        assertTrue(msg.contains("브랜치: feature/global-shortcut-menus-20261106"))
        assertTrue(msg.contains("커밋: 0123456789ab"))
        val absent=PythonOutcome.Success("🐍 Python 연결 정상 (v0.6.1)", false, true)
        assertTrue(ModuleSourceFormatter.statusDeployment(absent,true).contains("미기록"))
        assertTrue(ModuleSourceFormatter.statusDeployment(null,false).contains("미확인"))
        assertTrue(ModuleSourceFormatter.statusDeployment(PythonOutcome.Failure("연결 없음"),true).contains("미확인"))
    }
}
