# Piko NewX 한국어 작업본

[원본 빌드 프로젝트](https://github.com/crimera/piko-newx)를 기반으로 [개인 포크](https://github.com/ForUltraplayer/piko-newx)에서 Piko 설정과 추가 기능의 한국어 지원을 개발합니다. X 기본 화면 전체와 Morphe의 패치 이름 및 설명은 범위에 포함하지 않습니다.

| 약어 | 의미 |
| --- | --- |
| APK | Android 설치 패키지 |
| MPP | Morphe 패치 번들 |
| SDK | Android 개발 도구 모음 |

## v0.1.0

사용자가 휴대폰에서 Piko 설정 메뉴의 한국어 표시 성공을 보고한 **469 개 문구판**을 첫 한국어 배포판으로 제공합니다. [서명된 패치 파일](https://github.com/ForUltraplayer/piko-newx/releases/download/v0.1.0/piko-newx-korean-0.1.0.mpp)을 받을 수 있으며, 공개 설명은 [릴리스 설명](RELEASE_NOTES.md), 절차와 서명키 관리는 [배포 준비 기록](RELEASE_PREPARATION.md)에 정리합니다.

Android에서 아래 Morphe 추가 버튼을 누르거나 원격 소스로 `https://github.com/ForUltraplayer/piko-newx`를 등록하면 v0.1.0을 받을 수 있습니다. 이전에 같은 주소를 등록했다면 소스 카드에서 업데이트를 실행합니다.

## 개발 소스의 한국어 적용 범위

로컬 개발 소스에는 설정, 다운로드 선택기와 해상도 선택기, 이미지 병합 안내, 필터링된 답글, 추천 토픽 선택기, 다운로드 및 비정상 종료 알림, 개발자용 객체 탐색기의 문구 554 개가 준비돼 있습니다. 이 중 소스 빌드가 필요한 추가 문구 85 개는 이번 469 개 문구 배포판에 포함하지 않습니다. 기본 영어 리소스도 유지하며 Android의 앱 언어 설정에 따라 선택합니다. 내부 미디어 판별 값, 파일명 토큰, 서버 데이터와 코드 식별자는 원래 값을 유지합니다.

초기 단계의 설정 리소스 469 개에서, 소스에 직접 작성된 화면과 알림을 연결하는 문구 85 개를 추가했습니다. 공통 설정 화면은 기존 호스트의 리소스 선택을 사용하고, 다운로드 알림에는 공통 엔진의 번역 인터페이스를 구현한 공급자를 연결했습니다. 공통 라이브러리 자체는 교체하지 않습니다.

| 역할 | 구현 위치 |
| --- | --- |
| 한국어 번역 문구 | `locales/ko/newx/strings.xml` |
| 영어 추가 문구와 화면 및 알림의 리소스 연결 | `locales/newx-ui.patch` |
| 임시 소스에 패치 적용, 번역 검증 및 복사 | `build_piko.py`의 `apply_korean_resources()` |

Piko 소스의 `values-ko-rKR/newx/strings.xml`에 한국어 리소스를 추가하면 공통 리소스 로더가 APK의 `res/values-ko/strings.xml`에 반영합니다.

번역 기준은 Piko `x-lite`의 `48af8e1a7438e6d4d2f18ebe894acdcc0eeb7272`이며, 확인한 공통 라이브러리 버전은 `v0.10.1-dev.1`입니다. 빌드는 원본과 동일하게 최신 `x-lite`를 받습니다. 소스 패치를 적용할 수 없거나 번역 키가 추가 또는 삭제되면 중단합니다. 빈 번역과 서식 치환 문자 및 파일명 토큰 불일치도 검사합니다. 키와 치환 문자가 그대로인 원문 의미 변경은 수동 검토가 필요합니다.

## 검증 결과

2026 년 10 월 28 일 현재 다음 검증을 통과했습니다.

- 원본 소스에 패치 신규 적용 및 재적용 검사
- 한국어 554 개의 키, 치환 문자 및 파일명 토큰 일치
- 기존 영어 리소스 470 개의 값 보존
- 화면에서 참조하는 NewX 문자열의 영어 및 한국어 리소스 존재 확인
- 잘못된 치환 문자 유형을 주입했을 때 검증 실패 확인
- Android 리소스 컴파일러 AAPT2로 영어 및 한국어 XML 컴파일
- JDK 17 컴파일러의 파서로 수정한 Java 파일 15 개의 구문 검사
- Python 구문 검사 및 Git 공백 검사

전체 빌드는 `:patches:build --no-daemon`으로 시도했지만 Morphe Gradle 플러그인 `app.morphe.patches:1.3.4`를 해석하는 단계에서 실패했습니다. 같은 패키지 주소에 현재 GitHub 인증으로 요청했을 때 HTTP 401이 반환됐습니다. 따라서 전체 소스 빌드판의 Java와 Kotlin 타입 검사, 기존 Gradle 테스트, MPP 생성과 실제 Android 화면은 검증하지 못했습니다. 별도로 준비한 469 개 문구 리소스 시험판은 이후 사용자가 메뉴 한국어 표시 성공을 보고했습니다.

초기 확인에서는 PATH에 Java가 없었지만 이후 Gradle의 기존 JDK 17을 찾아 Gradle 실행에 사용했습니다. JDK 21과 Android SDK의 전체 빌드 준비 상태는 아직 확인하지 못했습니다. 빌드 로그는 이 PC의 `bins/build-validation.log`에 있으며, 검증용 Gradle은 빌드 종료 시 중지하는 옵션으로 실행했습니다.

## 알려진 한계와 배포 조건

### 휴대폰에서 설정 번역 시험

전체 소스 빌드와 별도로 공식 Piko 3.66.0 번들에 설정 번역 469 개만 추가한 시험 파일을 준비했습니다. 파일은 `dist/piko-newx-ko-resource-test-3.66.0.mpp`입니다. 공식 Morphe Desktop 1.19.1과 Temurin JRE 21로 불러왔을 때 패치 49 개가 정상적으로 나열됐습니다. 원본의 실행 코드 항목 727 개가 그대로인지와 ZIP 무결성도 확인했습니다. 이 파일에는 새 알림 코드 등을 연결한 문구 85 개는 적용되지 않습니다.

1. 시험 파일을 휴대폰으로 옮깁니다.
2. Morphe의 패치 소스 추가에서 로컬 파일을 선택하고 시험 파일을 불러옵니다. 휴대폰 파일 관리자에서 `.mpp` 파일을 Morphe로 열어도 됩니다.
3. 시험 소스만 선택하고 지원되는 원본 X 파일을 패치합니다. 기준 배포 메타데이터의 앱 버전은 `12.37.2-prod.01`입니다.
4. 기존 X와 별도로 설치하려면 `NewX: Clone`을 선택하고, 패키지명은 `com.twitter.android.piko.kotest`, 앱 이름은 `X Piko KO Test`로 지정합니다. 이 값은 시험용 제안입니다.
5. 설치한 앱의 언어를 한국어로 설정하고 앱을 다시 연 뒤 Piko 설정에서 한국어 표시를 확인합니다.

시험 파일은 `prepare_resource_test_bundle.py`로 생성하며, 기존 영어 번들과 실행 코드는 유지하고 한국어 리소스 및 시험 소스의 표시 정보만 추가합니다. 같은 폴더의 `.sha256` 파일로 체크섬을 확인할 수 있습니다. GitHub 주소를 등록해 받는 원본 릴리스에는 이 시험 파일이 반영돼 있지 않습니다. Morphe 앱 자체 메뉴와 X 기본 화면은 번역 대상이 아닙니다.

### 전체 소스 빌드의 남은 조건

공통 다운로드 라이브러리에는 재시도 버튼을 누른 직후의 임시 알림에 기본 영어 공급자를 사용하는 경로가 남아 있습니다. NewX에서 등록한 전송 알림 공급자는 한국어 리소스를 참조합니다. Android에서 실제 전환 동작과 화면 배치는 아직 확인하지 못했습니다. 서버가 반환한 토픽 이름, 계정 인증 유형, 예외 상세 내용과 개발자용 코드 정보에는 원래 언어가 표시될 수 있습니다.

추가 85 개 문구를 포함한 전체 소스 빌드에는 GitHub Packages에 접근 가능한 인증과 프로젝트의 빌드 도구가 필요합니다. 원본 릴리스 워크플로는 Linux, Java 21, Python 3.13과 GPG 분리 서명을 사용합니다. 이번 469 개 문구 배포판은 공식 번들을 기반으로 준비했으며 Morphe 내장 Ed25519 서명을 적용합니다. 로컬 `patches-bundle.json`은 한국어판 v0.1.0의 배포 주소와 공개키를 가리키도록 수정했습니다.

아래 명령은 이 PC에 받은 Piko 작업본에 한국어 소스 패치와 리소스를 적용하고 검증합니다. MPP나 APK를 생성하는 명령은 아닙니다.

```powershell
cd J:\Coding_project\twitter
python -c "from pathlib import Path; from build_piko import apply_korean_resources; print(apply_korean_resources(Path('bins/source/piko')))"
```

아래 버튼은 Android에서 한국어판의 Morphe 소스를 추가합니다.

<p align="center">
  <a href="https://morphe.software/add-source?github=ForUltraplayer/piko-newx">
    <img src="assets/add-to-morphe.svg" alt="Add to Morphe" height="48">
  </a>
</p>

Builds and publishes the [NewX](https://github.com/crimera/piko/tree/x-lite) patch bundle from the [Piko `x-lite` branch](https://github.com/crimera/piko/tree/x-lite).

# Credits
- [morphe](https://github.com/MorpheApp) - patcher
- [revanced](https://github.com/ReVanced) - previous patcher
- [j-hc](https://github.com/j-hc) - Project is inspired by j-hc's revanced builder template.
