# AngaeBot Bridge v0.1.2 — Gradle Wrapper HTTP 404 수정

기준 로컬 경로: `D:\stockproj\AngaeBotBridge`  
GitHub: https://github.com/nfwscho/AngaeBotBridge

## 문제 원인

기존 `scripts/prepare-wrapper.ps1`의 `https://services.gradle.org/distributions/gradle-8.14.3-wrapper.jar` 요청이 사용자 환경에서 HTTP 404를 반환했습니다. **Gradle 8.14.3이 존재하지 않는다는 의미가 아닙니다.** 공식 릴리스와 체크섬이 확인되어 Gradle 버전을 유지합니다.

## 변경 내용

- `scripts/prepare-wrapper.ps1`의 다운로드 서버를 `https://downloads.gradle.org/distributions/gradle-8.14.3-wrapper.jar` 우선으로 변경
- 첫 번째 서버 요청 실패 시 공식 GitHub Gradle 저장소 `v8.14.3` 태그의 wrapper JAR을 예비 소스로 사용
- 실제 파일을 임시 경로로 다운로드하여 SHA-256이 공식 체크섬과 **완전히 일치한 경우에만** `gradle/wrapper/gradle-wrapper.jar`로 저장
- 이미 정상 Wrapper JAR가 있으면 건너뛰고, 알 수 없는 JAR이 있으면 자동 덮어쓰기 금지
- 두 다운로드가 모두 실패하거나 체크섬 불일치 시 실패 원인을 출력 후 중단
- Kotlin 앱, AndroidManifest, 기존 UI/명령/로그/DB 로직 수정 없음

Gradle 8.14.3 Wrapper JAR 공식 SHA-256:  
`7d3a4ac4de1c32b59bc6a4eb8ecb8e612ccd0cf1ae1e99f66902da64df296172`  
공식 확인: https://gradle.org/release-checksums/

## 적용 순서 (Windows PowerShell)

**방법 A: 수정된 단일 스크립트만 교체 (추천)**

1. 제공한 `GPT_20261104_앙개봇_prepare-wrapper_v0.1.2.ps1` 파일을 다운로드합니다.
2. 파일 이름을 **`prepare-wrapper.ps1`**로 바꾼 다음 `D:\stockproj\AngaeBotBridge\scripts\` 에 복사해 기존 스크립트만 교체합니다.
3. 다음을 실행합니다.

```powershell
cd D:\stockproj\AngaeBotBridge
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1
(Get-FileHash .\gradle\wrapper\gradle-wrapper.jar -Algorithm SHA256).Hash.ToLowerInvariant()
.\gradlew.bat --version
.\gradlew.bat :app:assembleDebug
```

**방법 B: 전체 v0.1.2 ZIP에서 `scripts/prepare-wrapper.ps1`만 복사**해도 됩니다. 기존 Git 작업 폴더를 지우거나 `git init`을 다시 실행하지 마세요.

`gradlew.bat --version`부터 Gradle 8.14.3 **배포 ZIP 다운로드가 따로 시작**될 수 있으며, `gradle-wrapper.jar`(작은 부트스트랩 JAR)와는 별개입니다. 추가 오류가 나오면 그 오류 로그를 확인해야 합니다.

## GitHub 커밋

```powershell
cd D:\stockproj\AngaeBotBridge
git status
git diff -- scripts/prepare-wrapper.ps1
git add scripts/prepare-wrapper.ps1
git commit -m "fix: handle Gradle 8.14.3 wrapper download 404 (v0.1.2)"
git push origin main
```

커밋할 파일을 `scripts/prepare-wrapper.ps1`로 한정하면 다른 미완료 변경사항을 함께 올리지 않습니다.

## 확인되지 않은 부분

이 환경에는 Android SDK/실제 S20+가 없어서 APK 컴파일과 휴대폰 설치는 수행하지 않았습니다. 또한 외부 다운로드 서버에 대한 실제 네트워크 성공 여부도 사용자 Windows PC에서 확인해야 합니다.
