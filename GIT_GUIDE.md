> 앙개봇 실제 프로젝트 설정 (2026-11-04): `D:\stockproj\AngaeBotBridge`, GitHub `https://github.com/nfwscho/AngaeBotBridge.git`, 브랜치 `main`. 이 문서 아래의 `D:\AngaeBot` 및 `YOUR_GITHUB_ID`는 초기 설명용 예시이며, 실제 작업 시 위 값을 사용하세요. Git 재초기화 또는 remote 재등록 불필요.

# 앙개봇 Android Bridge — Git 및 GitHub 사용 가이드

기준: **앱 소스 v0.1.0** / **Git 준비 문서 패키지 v0.1.1 (2026-11-04)**

이 문서는 Windows 10/11 + PowerShell에서 기존 `AngaeBotBridge_v0.1` 프로젝트를 **GitHub 비공개 저장소(Private)**로 올리고, 이후 개발 이력을 안전하게 관리하는 절차입니다. GitHub 저장소에 실제로 업로드하는 작업은 사용자의 PC에서 수행해야 합니다.

> 보안: `local.properties`, 앱 로그/DB, `.env`, API 키, 개인 토큰, 서명 키, 생성 APK는 커밋 금지입니다. 파일을 삭제해도 이미 커밋한 Git 기록에서는 사라지지 않으므로, 노출된 키는 반드시 폐기/재발급해야 합니다. 최초 공개 전에 저장소 전체를 검토하세요.

## 0. 폴더 위치 결정

ZIP을 `D:\AngaeBot` 등에 풉니다. 아래에서 사용하는 예시 경로는 `D:\AngaeBot\AngaeBotBridge_v0.1`입니다. 반드시 **`.gitignore`와 `settings.gradle.kts`가 보이는 프로젝트 최상위 폴더**에서 명령을 실행합니다.

PowerShell:

```powershell
Set-Location 'D:\AngaeBot\AngaeBotBridge_v0.1'
Get-ChildItem -Force
```

다른 경로에 풀었다면 자신의 폴더 경로로 변경하십시오.

## 1. Git 설치 및 사용자 정보 등록

Git for Windows: https://git-scm.com/downloads/win

```powershell
git --version
git config --global core.quotepath false

# 현재 앙개봇 저장소에만 적용 (값을 반드시 본인 정보로 변경)
git config user.name 'YOUR_NAME'
git config user.email 'YOUR_GITHUB_EMAIL_OR_NOREPLY'

git config --list --local
```

GitHub에서 이메일을 공개하고 싶지 않으면 GitHub 계정의 Emails 설정에서 제공하는 `...@users.noreply.github.com` 주소를 사용합니다. `git config`는 GitHub 로그인과 무관하게 커밋 작성자 표시용입니다.

## 2. Gradle Wrapper 선택 준비

원본 v0.1에는 Gradle wrapper JAR가 동봉되어 있지 않습니다. 빌드 가능한 Git 저장소를 만들려면 아래 파일 생성이 권장됩니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1
```

준비 스크립트가 공식 배포 파일을 받고 SHA-256을 검증하면 `gradle\wrapper\gradle-wrapper.jar`가 생성됩니다. **검증에 성공했을 때만** 아래 `git add`에 포함시키세요. 네트워크 문제로 준비 실패해도 코드 업로드 자체는 가능하며, GitHub 복제 후 다시 스크립트를 실행해야 합니다.

## 3. Git 저장소 최초 생성 및 로컬 커밋

```powershell
# 최초 1회만 실행; 이미 .git 폴더가 있다면 이 명령은 생략
git init -b main

git status

# 제외 대상이 제대로 걸러지는지 점검
git check-ignore -v local.properties app\build\outputs\apk\debug\app-debug.apk

# 커밋할 파일 준비
git add .

# 꼭 검토: 개인 자료/토큰이 포함되지 않았는지 확인
git status --short
git diff --cached --stat
git diff --cached --check

# 이상 없을 때만 첫 커밋
git commit -m 'feat: initialize AngaeBot Android Bridge v0.1'
```

`git diff --cached --check`는 공백/패치 이상 여부만 검사합니다. 보안 스캔이 아니므로 `git status`와 커밋 대상 파일을 반드시 직접 확인해야 합니다. `git add .`는 무조건 안전한 명령이 아닙니다.

## 4. GitHub에 **빈 Private 저장소** 생성

1. https://github.com/new 접속, 로그인.
2. Repository name: `AngaeBot` (추천; 본인 원하는 이름 가능).
3. Visibility: **Private** 선택.
4. `Add a README file`, `.gitignore`, `Choose a license`는 **선택하지 않고 빈 저장소** 생성 (로컬에 이미 포함되어 있기 때문).
5. 화면에 보이는 HTTPS URL을 복사. 형식은 `https://github.com/본인아이디/AngaeBot.git`.

### 4-A. 추천: 일반 Git 명령으로 업로드

```powershell
# 실제 GitHub 사용자 ID로 변경: 아래는 예시 주소입니다.
git remote add origin https://github.com/YOUR_GITHUB_ID/AngaeBot.git

git remote -v
git branch --show-current
git push -u origin main
```

처음 `push`할 때 Git Credential Manager가 웹브라우저 로그인/승인을 요구할 수 있습니다. 일반 계정 비밀번호를 Git 명령창에 입력하여 인증하는 방식은 지원되지 않습니다. 브라우저 기반 로그인 또는 토큰/SSH 인증을 사용하세요. **토큰을 커밋하거나 URL에 직접 넣지 마세요.**

공식 참고: https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github

### 4-B. GitHub CLI(`gh`)가 이미 설치된 경우의 대안

아래는 **4-A 대신** 사용합니다. 이미 `origin`이 있거나 GitHub 웹에서 저장소를 만들었다면 중복으로 실행하지 마세요.

```powershell
gh auth login
gh repo create AngaeBot --private --source . --remote origin --push
```

한 번의 명령으로 생성과 push를 수행합니다. GitHub CLI 설치: https://cli.github.com/

## 5. 이후 소스를 수정할 때 (일반적인 5단계)

```powershell
Set-Location 'D:\AngaeBot\AngaeBotBridge_v0.1'
git status
git diff

git add .
git diff --cached --stat
git commit -m 'fix: improve Kakao notification parsing and logs'
git push
```

메시지 예시:

- `feat: add Python command bridge` — 기능 추가
- `fix: prevent duplicate Kakao replies` — 오류 수정
- `docs: update S20+ installation instructions` — 문서 수정
- `refactor: separate reply handling without behavior changes` — 구조 개선

실제로 수정한 내용에 맞는 커밋 메시지를 사용하세요. UI/기능/로그가 유지되는지도 별도 시험합니다.

## 6. 안전한 개발용 브랜치 (2단계 Python 연동 시 권장)

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/python-bridge

# 파일 수정 후
git add .
git commit -m 'feat: implement Python bridge transport'
git push -u origin feature/python-bridge
```

GitHub에서 **Pull Request**를 생성하고 코드를 검토·테스트한 뒤 `main`에 합칩니다. 브랜치 이름은 예시이며 상황에 맞게 바꿀 수 있습니다.

## 7. 릴리스 태그 (S20+ 실제 검증 후)

v0.1 소스는 현재 **Android SDK 컴파일 및 S20+ 실기기 시험 미완료** 상태이므로, `v0.1.0` 릴리스 태그는 검증에 성공한 뒤에 붙이는 것을 추천합니다.

```powershell
git switch main
git pull --ff-only origin main
git tag -a v0.1.0 -m 'AngaeBot Bridge v0.1.0: Android device verified'
git push origin v0.1.0
```

검증 전이라면 Git 태그를 만들지 않아도 GitHub에서 소스를 보관하고 개발할 수 있습니다.

## 8. 다른 컴퓨터에서 받아오기

```powershell
git clone https://github.com/YOUR_GITHUB_ID/AngaeBot.git
cd AngaeBot
powershell -ExecutionPolicy Bypass -File .\scripts\prepare-wrapper.ps1
```

정상 복제 후 `README.md`, `INSTALL.md`의 Android Studio 빌드 단계를 따릅니다.

## 9. 문제 해결

| 오류 또는 상황 | 원인/대응 |
| --- | --- |
| `'git'은(는) ... 명령이 아닙니다` | Git 설치 후 **PowerShell 새로 열기** |
| `fatal: not a git repository` | `Set-Location`으로 `.git`가 있는 프로젝트 루트 이동 |
| `Author identity unknown` | `git config user.name`, `git config user.email` 등록 |
| `remote origin already exists` | `git remote -v` 확인, 기존 URL을 바꿔야 할 때만 `git remote set-url origin ...` |
| `Repository not found` | GitHub 저장소 URL/소유자/Private 접근권한 확인 |
| `Authentication failed` | 브라우저 로그인, Git Credential Manager, PAT/SSH 인증 확인. GitHub 비밀번호로 push할 수 없음 |
| `rejected (fetch first)` | GitHub에 README 등 원격 초기 커밋이 있거나 누군가 먼저 push함. **강제 push 금지**. `git fetch origin` 후 이력 확인/병합 |
| 한글 경로가 이상하게 표시됨 | `git config --global core.quotepath false`와 PowerShell UTF-8 사용 확인 |
| `gradle-wrapper.jar` 없음 | `scripts/prepare-wrapper.ps1` 실행 후 체크섬 검증 확인 |
| 원치 않는 파일이 `git add`됨 | 커밋 전 `git restore --staged 파일경로`, `.gitignore` 갱신. 이미 추적된 파일은 `git rm --cached 파일경로`로 추적만 중단 |

## 10. 보안 및 업로드 전 최종 점검

```powershell
git status --short
git ls-files
git remote -v
```

기존 소스에는 개인 카카오톡 대화 내용이나 API 키가 포함되어서는 안 됩니다. 실제 운영 중 저장된 SQLite 로그 DB와 TXT 내보내기 자료는 원칙적으로 GitHub에 업로드하지 마세요. GitHub 저장소를 **Private**으로 만들었더라도 비밀정보 보관소는 아닙니다.

참고: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github
