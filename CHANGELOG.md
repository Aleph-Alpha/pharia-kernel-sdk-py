# Changelog

## [0.8.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.7.1...v0.8.0) (2025-03-27)


### ⚠ BREAKING CHANGES

* update package name from pharia-kernel-sdk-py to pharia-skill

### Features

* add chat_stream CSI function ([60afd5e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/60afd5ea42a57f67f56dc903962d99b8b8623e79))
* add completion_stream CSI function ([134c953](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/134c9539f892820d1dacaffd1ca3cbea43dd4cc6))
* implement ChatStreamResponse as context manager ([38ef434](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/38ef434f276fcebb7cc156f853a26b0276c8506c))
* implement CompletionStreamResponse as context manager ([8a168cc](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8a168cc0138229ccbdf70dd8703ada1b7a8990cc))
* include event data in error case ([e124881](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e124881a58e4abb5fb8a9f14df45b9c34df1b5b7))
* streamline streaming interface for completion and chat ([9e59394](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9e59394387365a5f49657ddc2406454d11c9a97a))
* update package name from pharia-kernel-sdk-py to pharia-skill ([f0a6250](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f0a625068b86579e826d0e422118d7559b2388ac))
* update pharia-skill-cli to use GitHub releases ([0f52bbf](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0f52bbfdd1d8f8d0d52333166b3a17f023e97f0f))


### Bug Fixes

* avoid using bindings for unstable types ([cc16098](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/cc160986f1afb3b49e7f3a03ab011285ff74742d))
* call super init on chat stream to poll first message ([2ae9f60](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2ae9f6066507082ee2b2b30a08cfb733feb2d2e8))
* chmod on wrong file ([6739d33](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/6739d33bab5c9cc45db857fe4561cecc1dc68cfd))
* do not use unstable feature in signatures ([4316900](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4316900539ff8cb29106d757cdc12a6bdac8f4a9))


### Documentation

* add apache-2.0 license ([61a126f](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/61a126f61c0ed9cabf292ca47a95acca663363c4))
* add comment about decorator usage pattern ([7b7f062](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/7b7f0625dec3a7bddeb3a99d3cd3fcaf7797a7c9))
* add links for registry ([29d83e7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/29d83e7d74d675169f1d8941d661f6daa01265d8))
* add prerequisites to quick_start ([9fb42c0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9fb42c0b4d72bc60f79f3f283bcfa325f1f6f6c9))
* cleanup invocation docs ([a3a710f](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a3a710f14fa503be8950e26e988ea583d248fcba))
* Fix broken link ([8748292](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8748292b128134b93f625c5074af2e800861ab22))
* improve core_concepts description of Skill ([21bc122](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/21bc122848fd65a75bfab270c89076f053f41284))
* pull in changes from other public docs ([c7cea97](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/c7cea974fed8e077cbf233f6b1f354ee1a9f64b7))
* refactor introduction and USP narrative ([3798d20](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3798d203c950f675f1a86a359a6a48c3bcbfc3ea))
* reference generator expression ([80c5c1e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/80c5c1e757d386d87ca89155e24345acec476de3))
* remove jfrog installation references ([7cf8530](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/7cf853033651437d344bb62e6c16e55ca62d3dec))
* remove jfrog token env variable ([0542d0e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0542d0eb8d8ab18b0c374dd31493bfa7e6b4c386))
* specify frozen flag when syncing dependencies ([4d55715](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4d55715f7e881905f0a42018e1ce017cad99d842))
* specify usage of unstable features in glue code ([1f7eecd](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1f7eecdb44750a676f753b15e21317737f6b0476))
* typo ([47f5fc8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/47f5fc88a98699255daa0ae4e9211e2d7963e969))
* typo ([cc44517](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/cc445174b459e5176d798c83aaa6f259d1a7581e))

## [0.7.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.7.0...v0.7.1) (2025-03-06)


### Documentation

* state that search and document relate to Document Index ([16779b6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/16779b614de273aec8afeeba50bfad307ed9fe14))

## [0.7.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.6.3...v0.7.0) (2025-03-03)


### ⚠ BREAKING CHANGES

* stabilize new chunking

### Features

* stabilize new chunking ([db0a330](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/db0a330119e24ee596027e0257654c9b0fb9b0b2))

## [0.6.3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.6.2...v0.6.3) (2025-02-27)


### Features

* add interactive publish to cli ([60ac743](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/60ac743d5cbcbcbbc7e8d1627ed007e0c30fd884))
* handle error if env vars for skill registry not set ([219f5a1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/219f5a1feaea5ed0000960135a06b7b9acd5c993))


### Bug Fixes

* do not import unstable wit params to not break componentize-py build ([00d657d](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/00d657d0e7885f3e581f28bab2edc90c57257ae0))
* update to use Pharia Studio project ID ([b2e5960](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/b2e596015c8f42139a294524633ffcd455203165))


### Documentation

* fix example types ([2aaba03](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2aaba0332dba84f88e3596e2dd05458454a3894b))
* fix typo ([243fa70](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/243fa70b6747169409ad81f911b0cc18fdb0450d))

## [0.6.2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.6.1...v0.6.2) (2025-02-24)


### Bug Fixes

* use three letter abbreviation for languages ([4b74ee3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4b74ee3121e09f37417ed7295c37c57ffa02bc07))

## [0.6.1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.6.0...v0.6.1) (2025-02-24)


### Features

* _explain beta ([de1af34](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/de1af34e98e7eb8f824840b217ef09b7baf3b2e8))
* add explain wit world and new bindings ([f98a402](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f98a4029486d08b9e059be9b50eb01925000272d))
* add stable support for explain in csi ([257aab3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/257aab34e653ffa27092896627af4931d4ca3e25))
* display publish CLI subcommand after successful build ([691a8de](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/691a8dea06255c76bacfea571285186ad0a1c6b0))
* migrate CLI to Typer ([75601e4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/75601e4ce0311e798a917e51bc2c6e470eb1fa86))
* remove log level ([a6c8684](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a6c8684ef997b12e4e30a8eb5388b97b453b6b90))
* support custom name when publishing Skill ([7f076e8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/7f076e84a4a3310aa923c373a4d3e05a8e901b88))
* update help message for CLI arguments ([ba668ea](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ba668eab00821967b5be84c2da9bc3668ce94450))


### Bug Fixes

* avoid using backslash in f-string expression to support older Python versions ([326b9cc](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/326b9cc1b07e6bfdcc5b051c4f681ffa93a7ad12))
* do not use bindings of unstable types ([3b7d394](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3b7d394e0c8258196e8498b0c8d31f17702c8d87))
* remove outdated Pydantic WASI wheels ([706fa0c](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/706fa0ce93bd0a3149e516bc795348efe45d52b5))

## [0.6.0](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.13...v0.6.0) (2025-02-13)


### ⚠ BREAKING CHANGES

* release 0.6.0

### Features

* release 0.6.0 ([e76647e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e76647ebcb1511f249d56478ff8dbeda331883d4))


### Bug Fixes

* import RootModel in decorator to avoid failing runtime import ([cc5d83a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/cc5d83a64113fa62ffc363036117edb6722d4f2e))

## [0.5.13](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.12...v0.5.13) (2025-02-13)


### Features

* support v0_3 wit world in SDK ([ee1db95](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ee1db955fdb533614dc498d916efd79bd0c3746f))


### Bug Fixes

* represent token as bytes type and add deserialization logic for dataclass ([ceb2be1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ceb2be1aad273858fa997a64476d8aa6fd79f0f0))
* require datetimes to be tz-aware, but not necessarily utc ([5b429f4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/5b429f4099d04f49603a26469e42d88a65f31960))


### Documentation

* minor typos ([a402e96](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a402e96f6d2010aead90fea128c9ef305d9c9cbd))

## [0.5.12](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.11...v0.5.12) (2025-02-06)


### Bug Fixes

* deserialization of completion dev csi request ([defef86](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/defef86e85d47303f028ac81035796829aa9e4c6))
* kernel expects lowercase roles ([ae49117](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ae49117e680f25b103fee76761b486da82d76c87))


### Documentation

* add copy button to code snippets ([edbec02](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/edbec021d3a1a5fccc6bc4f4c83bc9581d5e6153))
* add faq section ([4703807](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4703807e2f4a2dcdfaebc942052bd82d8ebd14f7))
* add missing env variables to quick start ([6912928](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/69129281a6313ad7448d742e5d21edab1c0b600c))
* add section about dependencies ([57b9ace](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/57b9ace324e493394fc98c8bd2072ecd1275c10d))
* fix imports in code examples ([1405dbe](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1405dbef62bf2459c9a2ae4360f95e526469d95c))
* fix install instruction in README ([fe78934](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/fe789346f5b37dc27d96d7776a31aa9d5505ea45))
* fix installation instructions in quick start ([82db0dd](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/82db0ddc77ec02304a16e09bda737cbc848da92c))
* give example of stub csi usage ([edd31c1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/edd31c12df3ae18bfc6645f9749d6d54f1bc4579))
* increase max width so code blocks are rendered on one line ([47604bd](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/47604bdedd1a54d8d6b0bfa7dc21e3b66e0b097c))
* link core concepts csi ([ecef4b6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ecef4b6da6bdcd64b50aeb1316cd79b4964f8298))
* make sidebar smaller ([0cc1ef1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0cc1ef1ba0730d7615e1d6adb5c02d814d48f89e))
* remove link to p-prod values file ([ec10ed5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ec10ed576a3004bed55809d42994e84f0a07d15b))
* remove skill development section from README ([ee2f0c4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ee2f0c419a0ce29706256959af43d5961f6c2c8e))

## [0.5.11](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.10...v0.5.11) (2025-01-28)


### Features

* support new uuid format for studio project ids ([9ce6fd3](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9ce6fd36094c7ffb926e8d73e46ca2039ee12e6e))


### Bug Fixes

* do not include sphinx in package dependencies ([e3edc87](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e3edc8793d6c7d534e62b8bb988b80ee610851e4))

## [0.5.10](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.9...v0.5.10) (2025-01-24)


### Bug Fixes

* parse message role when deserializing in dev csi ([46b7c3b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/46b7c3b415284a8fab7cedf0af5b4d809247dc92))

## [0.5.9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.8...v0.5.9) (2025-01-23)


### Features

* document can be requested from csi ([9753b05](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9753b059fd43e0ab8bb46e896b2085b2e9273e00))
* forward kernel error message for all status codes ([545dd0d](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/545dd0d6006f22bb3d1054d15dafad2419e1bf33))
* specify schema for tools ([eca847e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/eca847e013bbda6b49380c1302c41e448e0f0eac))


### Documentation

* add namespace section to core concepts ([8c8dad1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8c8dad12c54b818537c5ad19e56ca3d0bacf41d9))

## [0.5.8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.7...v0.5.8) (2025-01-21)


### Features

* add build in tools to chat request ([59dda00](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/59dda008f76bd6cbe16aeb97363a66db08f7e414))
* add helper method to construct message from tool response ([f85fde9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f85fde9a6e8aa4afa4c934b68ba4ddab59d7d176))
* add llama3 chat request and response ([2f16f4c](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2f16f4c834e24f682c536112fc228d0326e25b49))
* add run method to code interpreter ([2e240ee](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2e240ee191b0a0c0e3b30789559715fd388b76b3))
* built in tools are also specified as types ([9eac271](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9eac271846278898081a39ee56d65303f6de5f31))
* built in tools return typed arguments ([3d97d83](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3d97d83f1a91258e74dbbbd07345a363bb237348))
* chat function becomes method on request ([5ee58c6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/5ee58c6c903e0df8359a4077a8a39e28e1388f8c))
* convert tool calls to prompt again ([a5b1e8b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a5b1e8b3e8c2341c89fc6d5050ce58581977f233))
* custom tools are serialized to user prompt ([47e764d](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/47e764d7e5af6482e0dd41c4d1d5c12176082674))
* eval for function calling ([bb28f86](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/bb28f863c309d5e5a91d352be877ed45b7f26e2b))
* expose chat function fro llama module ([60128b2](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/60128b202960c3baa666d5b15f7ab14c1ee1d940))
* move system prompt out of message list ([08e4011](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/08e4011d9fb9180104d216e6829d3417407fc943))
* parse build in tool calls from reply ([03855f5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/03855f5d8dba0c077cc4d9f8c58822f8d46ba3ea))
* parse built in tool calls ([4eec237](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4eec237cc7a446e4d9c024534bd961f67c72c6b2))
* pass tool response back to the model, limit to one tool call for now ([a7325cf](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a7325cf6d77684c77e71e57380d52852d3d07496))
* provide current date to the model in system prompt ([2fc53bf](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2fc53bf571d513e9e152c97bb20a0c99787dfc62))
* provide custom init for dataclasses to deny setting the role ([f4bd081](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f4bd081392bd042239adfdeb0f2f30dc4157683c))
* put json based tools into system prompt ([9f35ed8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9f35ed8f7c8214935ea840226f9968d092ab3953))
* remove title key from serialized json schema ([11772bc](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/11772bcbc22d6b80d7628eccc4a9f35b746cc935))
* serialize built in tools as dict ([fb1b1c5](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/fb1b1c5b062318ff063754abdd2b43afe378def0))
* tool call result can be added to existing chat request ([1aba0d4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1aba0d471666e29dbd0b049d68d96f6b2526453b))
* validate function arguments with provided pydantic model ([b4d97e1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/b4d97e115cadaea3c7aba8a1cdadecddebddfcf7))


### Bug Fixes

* also serialize json function calls ([0475387](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/047538721eb2f6564132f9721baf5efdc19c318d))
* deserialization of tool call ([3b5a451](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/3b5a451b8443378bdc037c89ecc9b5e0bddac145))
* do not exclude role field from init which breaks pydantic 2.10 deserialization ([f376e32](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f376e326805b71356e9d56b520ec282838447e32))
* do not provide default implementation to avoid type errors ([26defd9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/26defd9a3c2d98881d0bea7fef5c69cf828a8085))
* import typed dict from typing extensions for version compatibility ([e4fa87c](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/e4fa87cf55a7fb1ffe65fd616faad864f77a5772))
* make tool response serializable ([113d645](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/113d6458c6fb25656309a1e2abd4a3b60a66f5ee))
* model dump of tool definition ([2b25b61](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2b25b618c5f5c2cd03422115abed2a54a675ff37))
* only render the tools in the first user message ([2502e04](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2502e0454680ad9cc0ef8a574a168a55d3255091))
* prompt rendering of tool call ([8f58be8](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8f58be882ab7cfe4baa2769572562078e22544b4))
* remove duplicate python tag definition ([0b8a0b9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/0b8a0b91aa6506ee3e0491acc5719c0a84e1d481))
* split assistant message into distinct classes and fix deserialization ([f9f8822](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/f9f8822e2cce3d361484951e53057696ab732439))


### Documentation

* add comment about whitespace stripping ([07513e9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/07513e9e504133a3df3ec4ea93b7af5727e244e0))
* add doc string for render tool call ([1bdb69e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/1bdb69e8659b91007f348f3b386586804ac36461))
* add links for tool output format ([951d96e](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/951d96ec0f684c985924855fe5c487c112b5e02c))
* add README.md about different purpose of docs sections ([29fa407](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/29fa407e7a3c461caf1345d447137b773d324e97))
* add section about function calling ([5546f61](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/5546f61ba212adb75c34799cbf3da1a3fef57453))
* always write skill in upper case ([95a57b9](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/95a57b9475249f72130353b09d0eb2c4533c01c3))
* fix outdated doc string on message module ([ad5fbfe](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ad5fbfe92b9d5753fa48615265f19cfda5af4d9d))
* fix typo ([9bf8ad1](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/9bf8ad1eab5bb5523083ce37c12ae54bc07f3cda))
* remove function call specific stuff ([50870e4](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/50870e401c32771f34114cfde1dde8d865f31b5d))
* remove image of exhausted sloth ([a2b042b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/a2b042be6d934e0c44b14960f89e24ac990de58c))
* remove llama submodule ([34263ff](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/34263ff1d5464a786591178b31d202b9b8b4b525))
* rename building to how-to ([894fd23](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/894fd23b39980b42c9434452a9218bd1989eca67))
* restructure read the docs, add a new theme and more content ([8eadc25](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/8eadc25d4d5e0bf4ba69f436b71e8b5ec16126e9))
* specify chat request abstraction ([d6d4077](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/d6d40775ba47277eb45134d8083a611363c9ddd0))
* specify why ipython is always activated if any tool is provided ([83e2a75](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/83e2a755b1e31ec0c6fbffc1489de0df0de00ec9))
* specify why json based tools are put into user prompt ([4c76c5b](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4c76c5b948d282b9c1976d03d507725e7858761d))
* streamline USPs ([306cd3a](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/306cd3a57e613230e109232efcf575b566077f53))
* use absolute image import path ([ee11eeb](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/ee11eeb2329d3d218526c45cd525b21cf77738c2))

## [0.5.7](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.6...v0.5.7) (2025-01-09)


### Bug Fixes

* specify sdist and wheel for poetry build to succeed ([2700a87](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/2700a870329275ccdf4ecbf726d91df191462475))

## [0.5.6](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/compare/v0.5.5...v0.5.6) (2025-01-09)


### Features

* forward json error message from dev csi ([48d1056](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/48d105682c32bae9cc7b539d94ecf16770fe67b3))
* support special tokens in completion ([decee64](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/decee649ba8663a02e089b9de3ebe8bea94ae06f))


### Bug Fixes

* specify package format type for pharia_skill ([4443294](https://github.com/Aleph-Alpha/pharia-kernel-sdk-py/commit/4443294d9f044f18cf8a4b07afb6aba4b2cb8ae4))

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
