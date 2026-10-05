# WarWarden Protocol

WarWarden의 C2, 관측 자산, 효과기 자산이 공유하는 MFS Protobuf v3 계약과
C++20 참조 구현이다. 이 저장소가 메시지 필드 번호, wire format, 공통 유효성
검사의 단일 원본이다.

## 구성

- `proto/mfs/icd/v3/mfs.proto`: 언어 중립 메시지 계약
- `cpp/include/c2`: 공용 C++ 메시지 모델, 코덱, 검증 API
- `cpp/src`: C++20 참조 구현
- `tests`: golden packet, round-trip, 오류 처리, 계약 검증 시험

## CMake에서 사용

소비 프로젝트는 이 저장소를 Git submodule로 고정하고 CMake 타깃을 연결한다.

```cmake
add_subdirectory(external/warwarden-protocol)
target_link_libraries(your_target PRIVATE WarWarden::Protocol)
```

기존 C++ 호출부와 단계적으로 분리할 수 있도록 공개 헤더와 타입은 현재
`c2` 네임스페이스를 유지한다.

## 빌드 및 시험

```powershell
cmake -S . -B build -A x64
cmake --build build --config Release --parallel
ctest --test-dir build -C Release --output-on-failure
```

스키마 검사에는 [Buf](https://buf.build/)를 사용한다.

```sh
buf lint
```

## 버전 정책

- 소비 프로젝트는 `main` 대신 릴리스 태그 또는 정확한 커밋을 고정한다.
- 호환 가능한 필드 추가는 현재 `mfs.icd.v3` 패키지에서 진행한다.
- 호환되지 않는 변경은 새 패키지 버전에서 진행한다.
- 삭제한 필드와 enum의 번호 및 이름은 `reserved`로 보존하고 재사용하지 않는다.

## 개발용 Pose 확장

`DevelopmentPoseCommand`(Envelope 14)와 capability bit 3은 현재 자산·세션에
PROJECT_FRAME 위치(m)와 방위(deg)를 설정하는 선택적 개발 기능이다.
기존 필드 번호를 유지하며 command_id, 유효시간, 유한 좌표와 0 <= 방위 < 360을 검증한다.
장비 동작/멱등 처리/권한은 소비 프로젝트의 책임이다.
