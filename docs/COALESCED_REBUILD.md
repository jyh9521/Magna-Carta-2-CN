# Coalesced 副本回写验证（2026-10-18）

## 实现边界

`tools/build_coalesced.py` 接受输入容器、变化计划和独立新输出。先验证整份输入 SHA256，再按稳定 ID 与期望原文精确修改物理行值。保留行尾、前缀、其他文档及重复键次序，保持原编码；重新计算序列化长度，并再提取全部 ID/值核对。保护标记与次序不得变化，拒绝物理换行/NUL，不自动翻译。

这是容器级回写，不是 ISO 重建、TOC 更新、字体补字或游戏部署支持。可变长度只获静态格式验证；首次运行实验应选等长字段，不改变 TOC 长度和包内偏移。输入原件和已有输出都不覆盖。

## 计划示例（全部自制）

```json
{
  "schema_version": 1,
  "input_sha256": "替换为实际输入完整SHA256",
  "resource": "synthetic.int",
  "entries": [
    {"id": "提取器生成的稳定ID", "source": "示例 {0}\\n", "translation": "测试 {0}\\n"}
  ]
}
```

```powershell
python tools/build_coalesced.py INPUT CHANGES.json --output build/rebuilt.int
python -m unittest discover -s tests -p test_build_coalesced.py -v
```

空 entries 的无修改重建必须逐字节一致。9 项合成测试覆盖可变长度、混合行尾、hash/原文/ID 防护、控制码与文件保护。

## 实际原版静态实验

当前韩版 D1 `MC2Game/Localization/Coalesced.int` 原 SHA256：
`179e265cfc9e6d3e9f2586abe75b5da303b2af9b8484079851dab72f9f7edb8c`。
候选定位：嵌入 `MC2UI.int` → `[ButtonA] Kick`，稳定 ID：
`coalesced:eca4c3906a7e3d00fe0ff6838f0fb2f5bc920c96065b0c8641fec559d5ad8d14`。
原韩文 3 个 UTF-16 单元；ASCII 标记 `KCK` 同为 3 单元。原与重建容器均 1495972 字节，仅 6 个字节不同，输出 SHA256：
`a83ca0d476ff8ac1c2bbb0dd3c43567e8dc48a2eeb5b6e8b64ad1096908007f4`。

另有同长度中文干运行样本，未部署也未判定显示成功。两份实际变化计划及完整源文仅在本地 build/poc-verification/，不进入 Git。当前仅证明容器级再提取一致，尚未证明运行时读取到此字段。

## 原版启动观察

本机现有模拟器已变为 `xenia/xenia_canary.exe`，不是先前 master xenia.exe；实测 build `canary_experimental@50e9c715d`，可执行 SHA256：
`e5e197f50a7ed1b6f94a927613d0510f31b528eacbec5b7dea4e5fa99c49ac0e`。

2026-10-18 用 Disc 1 ISO 启动，storage/content/cache 均指向 build/poc-runtime/ 独立目录。解锁后实际观察到标题与村庄场景，场景右下角出现韩文踢击提示；截图分别保存在 build/poc-verification/original-title.png、original-kick-scene.png，日志 original-runtime.log。这些是原版基线，**不是中文显示或修改生效证据**。

最初 capture-locked-screen.png 只是锁屏截图，不当游戏证据。Esc 退出游戏不表示暂停开发，后续允许继续操作游戏窗口。

## 下一验证顺序

1. 全量独立提取 D1，逐文件 hash 验证，与原 ISO 对应；保留 D2 不参与本实验。
2. 只在隔离副本替换一个等长 ASCII 标记，观察同场景，确认真实文本资源绑定。
3. 回退同一资源到原 hash，观察同一提示恢复。
4. 根据真实字体引用补字，重复中文/回退验收。原字体映射缺字情况见 FONT_RESEARCH.md。

此前已完成 D1 全量提取到 build/poc-game/disc1，2016 文件逐一 SHA256 一致。仍没有资源改动后的实际游戏验证结论；最终状态以追加实验记录为准。

## 隔离 ASCII 尝试记录

已在独立提取目录部署等长 KCK 容器并启动对应 default.xex，日志验证 HostPathDevice 使用该副本。捕获到村庄/片头画面，但这可能是标题待机演示；未获得 KCK 可见证据，不能判作资源绑定成功。Esc 退出后已将副本容器恢复到原 SHA256；文件回退成功，游戏同场景回退尚未验收。物理 Esc 会使本轮窗口控制工具中止，属于工具交互限制，不把它写成用户暂停开发。后续继续非窗口开发，并在允许的后续会话继续游戏验证。
