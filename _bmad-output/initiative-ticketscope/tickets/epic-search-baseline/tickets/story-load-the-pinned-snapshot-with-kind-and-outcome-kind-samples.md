# Kind samples: snapshot 2026.11.1 at threshold 3

Evidence for story 5 (load the pinned snapshot with kind and outcome). It lets a reader check that the kind split reads right at the default threshold of 3.

Method: every issue of the published `snapshot-2026.11.1` asset scored with core's `kind_score` over `jira_to_fences(body)`. Issues whose title, body or comments hold an OS user-name path (`C:\Users\…`, `/Users/…`, `/home/…`) were dropped first. Then `random.Random(5)` sampled 20 issues from the sorted score-2 pool (just below the threshold, so `short`) and 20 from the sorted score-3–4 pool (just above, so `log_heavy`).

Pool sizes after the exclusion: score 2: 67 issues; score 3–4: 67 issues.

## Short, score 2

| Key | Score | Title |
|---|---|---|
| [MCL-10131](https://bugs.mojang.com/browse/MCL-10131) | 2 | The Launcher keeps crashing |
| [MCL-10408](https://bugs.mojang.com/browse/MCL-10408) | 2 | JVM args set incorrectly on x86_64 platforms |
| [MCL-10499](https://bugs.mojang.com/browse/MCL-10499) | 2 | Fresh O.s Install. Crashes on Startup. |
| [MCL-10931](https://bugs.mojang.com/browse/MCL-10931) | 2 | Minecraft Laucher 1.6.89-j "java.lang.RuntimeException: Classpath file not found: /root/.minecraft/ms-starter.jar" error in Xubuntu |
| [MCL-11768](https://bugs.mojang.com/browse/MCL-11768) | 2 | minecraft twitch modpack crash. java hotspot error |
| [MCL-14682](https://bugs.mojang.com/browse/MCL-14682) | 2 | Invisible launcher |
| [MCL-15043](https://bugs.mojang.com/browse/MCL-15043) | 2 | Minecraft can't launch and can't installed a new version of minecraft |
| [MCL-18458](https://bugs.mojang.com/browse/MCL-18458) | 2 | 1.17 will not launch |
| [MCL-19244](https://bugs.mojang.com/browse/MCL-19244) | 2 | Launcher randomly quits |
| [MCL-2564](https://bugs.mojang.com/browse/MCL-2564) | 2 | No alpha or Beta versions in launcher (even local ones) |
| [MCL-2957](https://bugs.mojang.com/browse/MCL-2957) | 2 | Forgotten tweak class in the a1.2.6.json |
| [MCL-4505](https://bugs.mojang.com/browse/MCL-4505) | 2 | Stops at splash screen |
| [MCL-5264](https://bugs.mojang.com/browse/MCL-5264) | 2 | Vanila launcher issue |
| [MCL-5627](https://bugs.mojang.com/browse/MCL-5627) | 2 | View crash report link is not working |
| [MCL-6542](https://bugs.mojang.com/browse/MCL-6542) | 2 | Minecraft does not launch |
| [MCL-815](https://bugs.mojang.com/browse/MCL-815) | 2 | New minecraft launcher and 1.6.1 - no sound |
| [MCL-9424](https://bugs.mojang.com/browse/MCL-9424) | 2 | Launcher error linux |
| [MCL-9476](https://bugs.mojang.com/browse/MCL-9476) | 2 | The game crashed whilst initializing game. |
| [MCL-9506](https://bugs.mojang.com/browse/MCL-9506) | 2 | Minecraft Isn't Launching |
| [MCL-9968](https://bugs.mojang.com/browse/MCL-9968) | 2 | crash after assigning ram |

## Log-heavy, score 3–4

| Key | Score | Title |
|---|---|---|
| [MCL-10175](https://bugs.mojang.com/browse/MCL-10175) | 4 | Minecraft won't launch |
| [MCL-1026](https://bugs.mojang.com/browse/MCL-1026) | 3 | "java.net.SocketException: Permission denied: connect" on downloading Launcher |
| [MCL-1119](https://bugs.mojang.com/browse/MCL-1119) | 4 | unable to find valid certification path to requested target |
| [MCL-1230](https://bugs.mojang.com/browse/MCL-1230) | 3 | Unable to Install Launcher - FATAL ERROR: net.minecraft.bootstrap.FatalBootstrapError |
| [MCL-13622](https://bugs.mojang.com/browse/MCL-13622) | 3 | Error Opengl / Fullscreen |
| [MCL-13623](https://bugs.mojang.com/browse/MCL-13623) | 3 | Fullscreen error |
| [MCL-2225](https://bugs.mojang.com/browse/MCL-2225) | 3 | FATAL ERROR: Unable to download while being forced |
| [MCL-2392](https://bugs.mojang.com/browse/MCL-2392) | 3 | minecraft not start help me please |
| [MCL-2406](https://bugs.mojang.com/browse/MCL-2406) | 3 | My launcher can't start! Big error |
| [MCL-3148](https://bugs.mojang.com/browse/MCL-3148) | 3 | Minecraft Not Opening/Working |
| [MCL-3255](https://bugs.mojang.com/browse/MCL-3255) | 4 | Can't download minecraft, gives me an error. |
| [MCL-4519](https://bugs.mojang.com/browse/MCL-4519) | 3 | Minecraft 1.7.10 Launch Erorr |
| [MCL-4520](https://bugs.mojang.com/browse/MCL-4520) | 3 | Minecraft  Launch Erorr |
| [MCL-5085](https://bugs.mojang.com/browse/MCL-5085) | 3 | i cant use minecraft because of this |
| [MCL-5105](https://bugs.mojang.com/browse/MCL-5105) | 3 | The Launcher begins, after the world opens, it crashes |
| [MCL-5225](https://bugs.mojang.com/browse/MCL-5225) | 4 | i cant open my game because it says that my game is modded but it isnt |
| [MCL-554](https://bugs.mojang.com/browse/MCL-554) | 4 | Bootstrap error |
| [MCL-7752](https://bugs.mojang.com/browse/MCL-7752) | 4 | Never played Minecraft in a few weeks because of this |
| [MCL-7867](https://bugs.mojang.com/browse/MCL-7867) | 4 | The New launcher keeps crashing every time i try to join a server |
| [MCL-9369](https://bugs.mojang.com/browse/MCL-9369) | 3 | cannot start MCL |
