# Changelog

## [0.1.6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.5...v0.1.6) (2024-10-01)


### Features

* invalidate skill in namespace ([0fd142a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0fd142a30977b7224e29d59356d4e0c82810d23b))

## [0.1.5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.4...v0.1.5) (2024-10-01)


### Features

* log result of skill publishing to stdout ([07f1eed](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/07f1eed90eadd35427c2d6eaa437a30f1fc19960))

## [0.1.4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.3...v0.1.4) (2024-10-01)


### Features

* add error handling to subprocess runs ([3aa8363](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3aa8363370cf47999715d7886bee266e467fde9a))
* do not require .wasm extension when publish command ([702d1c7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/702d1c77921ebc2e478b847410ef26ee9ab260ab))

## [0.1.3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.2...v0.1.3) (2024-10-01)


### Features

* add cli commands for building and deploying ([3145f1b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3145f1b604cc77e1716b8d29362bd0e8fa1c20a0))

## [0.1.2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.1...v0.1.2) (2024-09-27)


### Bug Fixes

* invoke wasi csi before passing it to skill ([090b49d](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/090b49d61fd382c517c23677481c75bfb06f4d01))

## [0.1.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.0...v0.1.1) (2024-09-27)


### Features

* adapt to csi hosted on existing kernel url ([c33c9c2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/c33c9c2bc10e3a9f5eb5754caca73607260a2d13))
* cache requests session ([dfc52df](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/dfc52dfc65d7b17f610e9e5dfdfbea2c52814b1d))
* promote DevCsi as public API ([8657225](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/86572251a1b08a5efd62ddc35528fb33fb434ad5))
* show error message from HTTP request in DevCsi ([7c06274](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/7c062740c85e0fbef43f0b7470dbefccaa38b7e9))

## 0.1.0 (2024-09-27)


### Features

* add skill macro ([8272efa](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8272efa85556ae205971a2d092008b7d5213a2ca))
* add the skill.wit and the generated bindings to the module ([333fa97](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/333fa97b3831bc60d79dee20a52a8e802e74f144))
* assert that [@skill](https://github.com/skill) is only used once ([30f478b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/30f478bf118b116f8a15732e769273fb4773d9ca))
* correct error type if skill handling fails ([e90a2d9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e90a2d96c5434048391788117c767e9095ba5210))
* forward wit bindings to main sdk module ([176d0c3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/176d0c36899f4705f87a165f546e396794f39698))
* inject CSI as part of the skill decorator ([2cd7ad3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2cd7ad3dbfbe13085cf8104579d5a9ecdaf59215))
* integrate pydantic version 2.5.2 with WASI support ([f6f7d72](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f6f7d72264815197d5ab823e35962d316e5d8231))
* no longer necessary to find location of skill.wit ([35f6359](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/35f63595c55501f9b61db42d091e283c27682486))
* provide defaults for CompletionParams ([b5f33fb](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/b5f33fb39564b4df45e7d4f2331a72fca4a327e1))
* provide protocol for Csi ([092e3d7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/092e3d7c422897ed3bcb5713feb8aa410cbbe369))
* provide StubCsi for testing ([1138435](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1138435feb59254e584d34c08e2cfbbd75393e6d))
* skill decorator parses input to pydantic model ([180ae03](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/180ae0324a91bbb3c86d46fdef09bfad0a32be64))
* skill decorator serialize output as json byte string ([c94c525](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/c94c525a1339eee88884930f5924f0c6894b934e))
* use llama 3.1 prompt syntax in example ([6ca6f82](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/6ca6f8234868b5527633b9b1742d41c7481cee2c))


### Documentation

* add missing mkdir command ([13052af](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/13052af1e9fefda1b256893993f45abaecebab77))
* documentation to install from Artifactory PyPI ([510a40f](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/510a40fe5f2d58bf2de68bea714a3de51778d6e6))
* simplify call to componentize-py ([e8fd1e4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e8fd1e47bac4753ebd6cc649258721b405203073))
* trim example haiku skill output ([708015a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/708015a81ef98903847b2645187eb17396c33522))
* update skill development with pydantic ([0a33774](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0a337740fab9110338cfa8939eefa4f012166ddf))
