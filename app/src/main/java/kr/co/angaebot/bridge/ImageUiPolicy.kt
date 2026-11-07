/*
 * 앙개봇 Android 카카오톡 이미지 자동전송 UI 판단 정책 — 전체 기능/안전성
 * 1. 원래 ACTION_SEND로 앱 전용 PNG를 카카오톡에 공유하는 기능을 보존한다.
 * 2. 공유 대상 선택에서는 정확한 허용 방 이름 1개와 공유 화면 제목, 클릭 가능한 수신 항목을 확인한다.
 * 3. 수신 방을 실제로 선택한 후에만 이미지 전송 버튼을 검사하며 요청 전에 모든 검증 정보를 다시 확인한다.
 * 4. 카카오톡 사진 확인 화면에서 방 이름이 숨겨져도 앞 단계의 정확한 수신 방 선택 기록을 보존한다.
 * 5. 선택된 방이 보이는 경우 또는 사진 미리보기/미디어 확인 표시가 보이는 경우에만 전송한다.
 * 6. 이름 중복, 다른 방, 이미지 근거 없음, 버튼 모호함, 단계 미검증, 시간 제한 등은 모두 WAIT로 처리한다.
 * 7. 기존 텍스트 알림 ReplyManager, Python Core/DB/UI/로그·허용목록은 변경하지 않는다.
 * 8. 이 순수 Kotlin 정책은 실제 카카오톡 수신을 증명하지 않으며 UI 실기기 검증을 요구한다.
 * 9. v0.4.19에서 '1 보내기' 같은 카운트 버튼을 지원하되 '2 보내기' 등 복수 선택을 차단한다.
 */
package kr.co.angaebot.bridge

internal enum class ImageUiStage { PICK_ROOM, CONFIRM_IMAGE }
internal enum class ImageUiAction { WAIT, CLICK_ROOM, CLICK_SEND }

internal data class ImageUiSnapshot(
    val visibleLabels: List<String>,
    val clickableRoomCount: Int,
    val clickableSendCount: Int,
    val selectedRoomVerified: Boolean = false,
    val afterRoomClick: Boolean = false,
    val largeImagePreviewVisible: Boolean = false,
    val explicitSendControlVisible: Boolean = false
)

internal object ImageUiPolicy {
    private val pickerLabels = setOf("채팅방", "대화방", "친구", "공유", "전송 대상", "보낼 대상")
    private val mediaLabels = setOf("사진", "이미지", "첨부", "사진 전송", "사진 보내기", "미리보기", "이미지 미리보기")

    fun action(stage: ImageUiStage, exactRoom: String, ui: ImageUiSnapshot): ImageUiAction {
        if (exactRoom.isBlank() || exactRoom.length > 100) return ImageUiAction.WAIT
        val labels = ui.visibleLabels.map { it.trim() }
        val exactRoomCount = labels.count { it == exactRoom }
        if (exactRoomCount > 1 || labels.any { ImageSendButtonLabel.isOtherCount(it) }) return ImageUiAction.WAIT
        return when (stage) {
            ImageUiStage.PICK_ROOM ->
                if (exactRoomCount == 1 && ui.clickableRoomCount == 1 && labels.any { it in pickerLabels })
                    ImageUiAction.CLICK_ROOM else ImageUiAction.WAIT
            ImageUiStage.CONFIRM_IMAGE -> {
                if (!ui.selectedRoomVerified || !ui.afterRoomClick || ui.clickableSendCount != 1) return ImageUiAction.WAIT
                val sendExplicit = ui.explicitSendControlVisible || labels.any { ImageSendButtonLabel.matches(it) }
                val mediaConfirmed = exactRoomCount == 1 ||
                    ui.largeImagePreviewVisible || labels.any { it in mediaLabels }
                if (sendExplicit && mediaConfirmed) ImageUiAction.CLICK_SEND else ImageUiAction.WAIT
            }
        }
    }
}
