/*
 * 앙개봇 실제 이미지 자동전송 UI 정책 회귀 테스트 — 전체 검증 기능
 * 1. 정확한 수신 채팅방 이름이 공유 UI에 하나만 존재할 때에만 대상 선택 가능 여부를 검증한다.
 * 2. 다른 채팅방, 비슷한 이름, 중복 이름, 방 이름 없음, 공유 화면 단서 없음에서는 전송 클릭을 차단한다.
 * 3. 확인 단계에는 같은 방 이름과 사진 첨부 단서 및 단일 전송 버튼이 모두 요구됨을 검증한다.
 * 4. 테스트는 실제 카카오톡을 조작하지 않으며 기존 Android/Python/PowerShell 테스트를 보존한다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertEquals
import org.junit.Test

class ImageUiPolicyTest {
    @Test fun onlyUniqueExactRoomCanBeSelectedInSharePicker() {
        val valid = ImageUiSnapshot(listOf("채팅방", "앙개봇 시험방"), 1, 0)
        assertEquals(ImageUiAction.CLICK_ROOM, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "앙개봇 시험방", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "다른방", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "앙개봇", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "앙개봇 시험방",
            ImageUiSnapshot(listOf("앙개봇 시험방"), 1, 0)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.PICK_ROOM, "앙개봇 시험방",
            ImageUiSnapshot(listOf("채팅방", "앙개봇 시험방", "앙개봇 시험방"), 2, 0)))
    }

    @Test fun sendNeedsExactRecipientMediaAndUniqueButton() {
        val valid = ImageUiSnapshot(listOf("사진", "앙개봇 시험방", "보내기"), 0, 1)
        assertEquals(ImageUiAction.CLICK_SEND, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "앙개봇 시험방", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "다른방", valid))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "앙개봇 시험방",
            ImageUiSnapshot(listOf("앙개봇 시험방", "보내기"), 0, 1)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "앙개봇 시험방",
            ImageUiSnapshot(listOf("사진", "앙개봇 시험방", "보내기"), 0, 2)))
        assertEquals(ImageUiAction.WAIT, ImageUiPolicy.action(ImageUiStage.CONFIRM_IMAGE, "앙개봇 시험방",
            ImageUiSnapshot(listOf("사진", "앙개봇 시험방", "보내기", "앙개봇 시험방"), 0, 1)))
    }
}
