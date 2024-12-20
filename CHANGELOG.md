# Changelog

## [0.5.5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.4...v0.5.5) (2024-12-20)


### Features

* update internal string representation of role enums to lower case ([ecd85bc](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ecd85bcc4e78ee783199d774650dae4ca599f026))


### Documentation

* add section about exposing internal types ([57f5dd0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/57f5dd0baff803374e2db4c4da2e90d04af796ea))

## [0.5.4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.3...v0.5.4) (2024-12-17)


### Features

* add document metadata to csi protocol ([f030990](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f030990410da54ddb374359d48874807928f40a2))
* add unstable option for building ([fcb29ae](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/fcb29aee98af298d8fca5bb64649bceaa056ba7a))
* implement document metadata for WASI CSI ([9de4a55](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9de4a550c4e79f965033aebc428d17de710b30d7))


### Documentation

* add command to generate bindings with unstable features ([08c93dc](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/08c93dc662a3ad6ed7105e076e90dde6e3595675))

## [0.5.3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.2...v0.5.3) (2024-12-10)


### Features

* bump cli version to latest ([e2fc319](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e2fc319ea7468be676cd17b4965ff767090064c9))

## [0.5.2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.1...v0.5.2) (2024-12-10)


### Features

* allow specifying skill tag ([6be9f16](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/6be9f165599166518530278fbe0c6f87fb3b2878))

## [0.5.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.0...v0.5.1) (2024-12-09)


### Bug Fixes

* incompatible method override ([4a6cbf8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4a6cbf8be15d1fb6d18c198bb4c556709756e9e9))

## [0.5.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.4.1...v0.5.0) (2024-12-05)


### ⚠ BREAKING CHANGES

* rename env variable to Pharia AI token

### Features

* rename env variable to Pharia AI token ([683e270](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/683e270cd422cb273a9c08b806483eb8a3c32436))


### Bug Fixes

* migration ([1551931](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1551931adc30861eb1f3463a9e64a557bb845a7c))


### Documentation

* update example Pharia Kernel endpoint ([8959f48](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8959f48355083cfb0704da27c896ab3946a609f0))

## [0.4.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.4.0...v0.4.1) (2024-11-28)


### Bug Fixes

* create projects in studio on dev csi creation ([00f9814](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/00f981494920df3348aa6826b658a4447ce713f0))

## [0.4.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.3.4...v0.4.0) (2024-11-28)


### ⚠ BREAKING CHANGES

* change *PASSWORD to *TOKEN

### Features

* change *PASSWORD to *TOKEN ([c7c9e78](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/c7c9e784b988c05c93741b1899fe9d6b40f4d8fb))
* replace JFROG_PASSWORD by JFROG_TOKEN ([94ceca2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/94ceca20c6384709fe1065c39e375d82d4dcb1d1))


### Documentation

* Replace password with token in skill registry ([451138a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/451138a43fad3fa220f16c66bd4857f7f310fc31))

## [0.3.4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.3.3...v0.3.4) (2024-11-20)


### Documentation

* Add testing and studio modules to documentation ([dc0738e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/dc0738e73945ce324d48231cdef02c20993cd2eb))
* remove duplicate requests from haiku example ([9d652a8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9d652a810dd67184db86c22316dc56eb23367606))
* update documentation and module structure ([79ded72](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/79ded72fb0c6c263335059d5b85414af926b0b6d))
* update README with link to Pharia Kernel ([0e28a74](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0e28a741ec0efba7c789fc155840cb268f185ce1))

## [0.3.3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.3.2...v0.3.3) (2024-11-19)


### Features

* always overwrite existing trace exporter ([4d27a86](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4d27a86a5427ed18b53c725744d8a4381e642f02))
* dev csi eports optl spans ([49ca5bf](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/49ca5bf746ff6c945be00216fce5acd742eded18))
* DevCsi offers flush collector method ([b63aca7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/b63aca735c3b2f9e36c1c021b33c5c9a4be99baf))
* DevCsi offers helper to set up studio exporter ([8387ff2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8387ff214005d6c0f911b02b2de768b5eb9cd320))
* make sure only one studio exporter is registered per thread ([f50aee7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f50aee797d9f3f591b5907e8ddabba9bfd1e1a20))
* more explicit event name for exceptions ([8dd902a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8dd902a48c44c80e165e6bbce3f11c78148646f7))
* provide translation between otel traces and studio format ([88d137e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/88d137ebc621a4232f33814181fbf22cae53c745))
* set error message for studio event message field ([3543133](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3543133e2dd6f264f7b00ce68fa968243b393270))
* upload traces as soon as root span ends ([cbc7149](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/cbc71498ccb5498e790f5d9a185e961cf8de90f8))


### Bug Fixes

* allow arbitrary input/output for tracing ([80fbe76](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/80fbe767174eddd22fd5d06d833399c190464612))
* do not include function and version in trace ([118c154](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/118c1546e2b3e7b807d8bf0d41f060fde32e48e7))
* submit spans in trace batches ([f39abc8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f39abc8acbfe414c263d12572506e3fe763e74c3))


### Documentation

* add doc string to with_studio method ([38c20b7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/38c20b76b2d3f529cf2c457477439ee2ebcb7136))
* add example of how to do tracing with studio ([6598d85](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/6598d85d79e6ee1351949ff2fb11008025d7e676))
* use double quotes in code example multi line string ([44ff2d8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/44ff2d8d4373c5ec1709e8cfb609f2fa8f16eeaf))

## [0.3.2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.3.1...v0.3.2) (2024-11-18)


### Documentation

* add docs section in poetry extra for sphinx ([71703ed](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/71703ed371a0234aa363bfe838cfb55997b65c99))
* add link to SDK documentation ([4494ecf](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4494ecf722c0f8db574001db597953c11e9609e3))
* Add Sphinx documentation and Read the Docs configuration. ([79ea956](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/79ea9569232508d06cb9d2b38f675895af6080ae))
* update CSI protocol and skill decorator ([349fc4b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/349fc4b46133b47d63765bdc13253c4dca056b01))

## [0.3.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.3.0...v0.3.1) (2024-11-15)


### Features

* add Heidelberg example and test show casing rag ([3d9350b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3d9350b01d108f38abfd2b0bbfd29621de9d2114))
* Add summarization skill and tests in examples ([496efa2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/496efa2f2957c7300afe3d94b8704f69f1422d40))
* make min_score parameter optional ([a3089d6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a3089d612c4defdcff3ee8a1315f9c8f65662b53))


### Documentation

* doc strings on csi functions added ([e4945d6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e4945d68460f33139434728137bea3ff8ac5f264))
* simplify csi imports and add missing dataclasses ([be1708a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/be1708abc1630fef51105f901d084a29c1a4d112))
* update haiku.py to use BaseModel ([5e9e650](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/5e9e6507cdbb224c4e295fac8f9e516afdfbef4a))
* Update pharia-skill-cli binary check, pydoclint suggestion ([917e0a6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/917e0a6006f9c7e09f42b4f2394dd7b03e88207c))

## [0.3.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.8...v0.3.0) (2024-11-11)


### ⚠ BREAKING CHANGES

* only allow pydantic output models
* support pydantic models, str and none as output

### Features

* handler can report input schema ([65ff839](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/65ff83939175073939bf52ae4477c6a035725a7c))
* only allow pydantic output models ([aeb9805](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/aeb98057b90bda6409d22c64868910c44142b883))
* skill handler reports output schema ([017115a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/017115a435d3b6356881c1198d19d9819a5e3283))
* support pydantic models, str and none as output ([a9e6205](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a9e62057fca853dbf71ee29a1d8cb0b45b3af17a))


### Documentation

* remove outdated WASI dependencies ([93aebd5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/93aebd5b34301b2a8e2a1950fc351f4d48645bcd))

## [0.2.8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.7...v0.2.8) (2024-11-07)


### Bug Fixes

* windows support, path and no chmod ([ba93958](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ba939588c31573ea1f7ca6f10313b1400a7b0534))

## [0.2.7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.6...v0.2.7) (2024-11-07)


### Features

* check for platform.machine on darwin systems ([16a39e3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/16a39e31bbd483e64154df0ccdbaeb23324044ea))
* use pharia-skill-cli jfrog binary ([6a477fb](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/6a477fbbc4d64434161e05a081e77d8a6971c76b))


### Bug Fixes

* forward exit code from subprocess ([2ee7e29](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2ee7e29b5632eb99bea50d3c06a1e15b750cec64))

## [0.2.6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.5...v0.2.6) (2024-11-04)


### Features

* update ruff to 7.2.0 ([30cb1f5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/30cb1f58ae5708d7bfebee247a48f52d3a7d4f0c))

## [0.2.5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.4...v0.2.5) (2024-10-30)

### Bug Fixes

* only close session if set ([76383c5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/76383c5eec7f3f618dee7a7569383789c6970a08)). This prevents a second exception to be raised if the  init fails if e.g. an env variable is not set.

## [0.2.4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.3...v0.2.4) (2024-10-25)


### Bug Fixes

* remove Err dataclass and use wit.types Err ([eb54df3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/eb54df392b0be110ac7868fbb6a40a46295f8d9f))

## [0.2.3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.2...v0.2.3) (2024-10-25)


### Bug Fixes

* translation of wasi role which caused skill runtime errors ([e49c58e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e49c58e3ff9cf455195b6cd925f59262802e9081))

## [0.2.2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.1...v0.2.2) (2024-10-24)


### Features

* csi owns message and chat response classes ([567dde6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/567dde6cafa4cdd2003bb48e1c78c0168805f80e))

## [0.2.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.2.0...v0.2.1) (2024-10-23)


### Features

* add chat support ([544b3f5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/544b3f5f97cef35d38865412042d3523dfac42ef))

## [0.2.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.8...v0.2.0) (2024-10-18)


### ⚠ BREAKING CHANGES

* allow providing skill registry user name to broaden registry support

### Features

* allow providing skill registry user name to broaden registry support ([018f057](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/018f0573530fe8d491b6f4d63572e580c8005e65))

## [0.1.8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.7...v0.1.8) (2024-10-18)


### Features

* expose all csi interfaces toplevel ([cc9cd23](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/cc9cd23a42c24c1b31d933714e57d5baec6c6d91))

## [0.1.7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.1.6...v0.1.7) (2024-10-18)


### Features

* add search to csi ([aaad8ed](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/aaad8ed9b8940b1e916b762d2c8e4449e3d43072))

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
