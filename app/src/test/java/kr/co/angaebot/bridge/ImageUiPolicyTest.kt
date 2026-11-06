/*
 * 앙개봇 이미지 전송 최종 버튼 자동 클릭 정책 전체 회귀 테스트
 * 1. 공유 화면에서 수신 방을 정확하게 식별하고 선택할 때만 다음 단계로 진입하는지 검증한다.
 * 2. 사진 확인 화면에 방 이름이 다시 표시되지 않아도 확인된 수신 방과 사진 미리보기로 보내기를 허용한다.
 * 3. 같은 화면에 수신 방 이름이 남고 전송 버튼만 나타나는 공유 UI도 처리한다.
 * 4. 중복/다른 방, 방 선택 기록 부재, 너무 빠른 상태, 잘못된 확인 버튼, 사진 증거 부재를 안전하게 차단한다.
 * 5. 기존 Android/Kotlin/Windows/Python 테스트와 카카오톡 로그/상태/UI는 모두 보존한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Test

class ImageUiPolicyTest {
    private val room = "앙개봇 시험방"

    @Test fun onlyUniqueExactRoomCanBeSelectedInSharePicker() {
        val valid = ImageUiSnapshot(listOf("채팅방", room), 1, 0)
        assertEquals(ImageUiAction.CLICK_ROOM, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, room, valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "다른방", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "앙개봇", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, room,
            ImageUiSnapshot(listOf(room), 1, 0)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, room,
            ImageUiSnapshot(listOf("채팅방", room, room), 2, 0)))
    }

    @Test fun finalSendInSamePickerWorksAfterExactRoomSelection() {
        val selected = ImageUiSnapshot(listOf("채팅방", room, "보내기"), 1, 1,
            selectedRoomVerified = true, afterRoomClick = true)
        assertEquals(ImageUiAction.CLICK_SEND, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room, selected))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "다른방", selected))
    }

    @Test fun imagePreviewCanHideRecipientAfterVerifiedSelection() {
        val preview = ImageUiSnapshot(listOf("이미지 미리보기", "보내기"), 0, 1,
            selectedRoomVerified = true, afterRoomClick = true, largeImagePreviewVisible = true)
        assertEquals(ImageUiAction.CLICK_SEND, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room, preview))
        assertEquals(ImageUiAction.CLICK_SEND, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            preview.copy(visibleLabels = listOf("보내기"))))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            preview.copy(selectedRoomVerified = false)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            preview.copy(afterRoomClick = false)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            preview.copy(clickableSendCount = 2)))
    }

    @Test fun incompleteOrAmbiguousPreviewNeverSends() {
        val base = ImageUiSnapshot(listOf("보내기"), 0, 1,
            selectedRoomVerified = true, afterRoomClick = true)
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room, base))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            base.copy(visibleLabels = listOf("확인"), largeImagePreviewVisible = true,
                explicitSendControlVisible = false)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            base.copy(visibleLabels = listOf("보내기", room, room))))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            base.copy(clickableSendCount = 0, largeImagePreviewVisible = true)))
    }

    @Test fun accessibleSendIconRequiresPreviewEvidence() {
        val base = ImageUiSnapshot(listOf("사진"), 0, 1,
            selectedRoomVerified = true, afterRoomClick = true,
            explicitSendControlVisible = true, largeImagePreviewVisible = true)
        assertEquals(ImageUiAction.CLICK_SEND, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room, base))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, room,
            base.copy(explicitSendControlVisible = false, visibleLabels = listOf("미리보기"))))
    }
}
