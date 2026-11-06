/*
 * 앙개봇 카카오톡 실제 이미지 자동전송 UI 판단 정책 — 전체 기능/안전성 상세 주석
 * 1. 기존 NotificationListener/RemoteInput 텍스트 자동응답과 독립된 사진 공유 화면 판단만 수행한다.
 * 2. 사용자가 허용한 정확한 채팅방 이름을 UI 텍스트와 일치 비교한다. 부분 일치나 다른 방은 선택하지 않는다.
 * 3. 사진 공유 대상 선택 화면이라는 단서와 유일한 클릭 가능한 방 이름이 함께 확인될 때만 방 선택을 허용한다.
 * 4. 이어지는 확인 단계도 같은 방 이름과 유일한 보내기 버튼, 사진 첨부 화면 단서가 동시에 있어야 클릭을 허용한다.
 * 5. 화면 정보가 누락/중복/모호하거나 잠금 등으로 중단될 때는 아무 버튼도 누르지 않는다.
 * 6. 모든 판단은 순수 Kotlin이며 서버/카카오톡/SQLite/설정/로그/이미지 데이터에 직접 접근하지 않는다.
 * 7. 이 정책의 성공은 접근성 조작 요청 판단일 뿐 실제 카카오톡 전송 성공 증거는 아니다.
 */

package kr.co.angaebot.bridge

internal enum class ImageUiStage { PICK_ROOM, CONFIRM_IMAGE }
internal enum class ImageUiAction { WAIT, CLICK_ROOM, CLICK_SEND }

internal data class ImageUiSnapshot(
    val visibleLabels: List<String>,
    val clickableRoomCount: Int,
    val clickableSendCount: Int
)

internal object ImageUiPolicy {
    private val pickerLabels = setOf("채팅방", "대화방", "친구", "공유", "전송 대상", "보낼 대상")
    private val mediaLabels = setOf("사진", "이미지", "첨부", "사진 전송", "사진 보내기")
    private val sendLabels = setOf("전송", "보내기", "확인")

    fun action(stage: ImageUiStage, exactRoom: String, ui: ImageUiSnapshot): ImageUiAction {
        if (exactRoom.isBlank() || exactRoom.length > 100) return ImageUiAction.WAIT
        val labels = ui.visibleLabels.map { it.trim() }
        if (labels.count { it == exactRoom } != 1) return ImageUiAction.WAIT
        return when (stage) {
            ImageUiStage.PICK_ROOM ->
                if (ui.clickableRoomCount == 1 && labels.any { it in pickerLabels })
                    ImageUiAction.CLICK_ROOM else ImageUiAction.WAIT
            ImageUiStage.CONFIRM_IMAGE ->
                if (ui.clickableSendCount == 1 &&
                    labels.any { it in mediaLabels } &&
                    labels.any { it in sendLabels })
                    ImageUiAction.CLICK_SEND else ImageUiAction.WAIT
        }
    }
}
