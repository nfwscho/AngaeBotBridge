/*
 * 앙개봇 카카오톡 이미지 전송 버튼 라벨 회귀 테스트 — 전체 기능
 * 1. 기존 단일 전송 라벨과 영어 버튼 이름 인식을 보존한다.
 * 2. 현재 S20+ 공유 화면에 실제 표시된 '1 보내기' 및 공백/줄바꿈 변형을 검증한다.
 * 3. 0/2/10 등 한 명이 아닌 대상 수와 모호한 버튼/팝업을 전송 대상에서 제외한다.
 * 4. 실제 카카오톡·S20+/Python/DB/로그/UI/설정에는 접근하지 않는 순수 단위 테스트다.
 */
package kr.co.angaebot.bridge

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ImageSendButtonLabelTest {
    @Test fun singleRecipientLabelAndOldButtonsWork() {
        for (label in listOf("보내기", "전송", "전송하기", "사진 보내기", "사진 전송",
                "이미지 보내기", "Send", "Send photo",
                "1 보내기", "1보내기", " 1  보내기 ", "1\n보내기", "1 전송")) {
            assertTrue(label, ImageSendButtonLabel.matches(label))
            assertFalse(label, ImageSendButtonLabel.isOtherCount(label))
        }
    }

    @Test fun multipleRecipientsAreNeverAllowed() {
        for (label in listOf("0 보내기", "2 보내기", "3보내기", "10 전송", "01 보내기")) {
            assertFalse(label, ImageSendButtonLabel.matches(label))
            assertTrue(label, ImageSendButtonLabel.isOtherCount(label))
        }
    }

    @Test fun unrelatedLabelsDoNotMatch() {
        for (label in listOf("확인", "취소", "보내기 안내", "사진을 보내기",
                "보내기 2", "메시지를 입력해 주세요.", "다른 사람에게 전송", "")) {
            assertFalse(label, ImageSendButtonLabel.matches(label))
            assertFalse(label, ImageSendButtonLabel.isOtherCount(label))
        }
    }
}
