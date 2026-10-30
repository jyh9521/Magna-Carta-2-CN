import 'dart:io';

import 'package:flutter/material.dart';

import 'backend.dart';
import 'desktop.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const InstallerApp());
}

class InstallerApp extends StatefulWidget {
  const InstallerApp({super.key, this.backend});
  final Backend? backend;
  @override
  State<InstallerApp> createState() => _InstallerAppState();
}

class _InstallerAppState extends State<InstallerApp> {
  bool dark = true;
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: '《真名法典2》简体中文汉化补丁',
    theme: installerTheme(Brightness.light),
    darkTheme: installerTheme(Brightness.dark),
    themeMode: dark ? ThemeMode.dark : ThemeMode.light,
    home: InstallerHome(
      backend: widget.backend,
      dark: dark,
      onTheme: () => setState(() => dark = !dark),
    ),
  );
}

class InstallerHome extends StatefulWidget {
  const InstallerHome({
    super.key,
    this.backend,
    required this.dark,
    required this.onTheme,
  });
  final Backend? backend;
  final bool dark;
  final VoidCallback onTheme;
  @override
  State<InstallerHome> createState() => _InstallerHomeState();
}

class _InstallerHomeState extends State<InstallerHome> {
  late final Backend backend;
  final disc1 = TextEditingController(), disc2 = TextEditingController();
  final dlc = TextEditingController(), output = TextEditingController();
  final form = GlobalKey<FormState>();
  int step = 0;
  bool includeDlc = true, checked = false, showErrors = false;
  String format = 'zar', logFilter = 'all';
  @override
  void initState() {
    super.initState();
    backend = widget.backend ?? Backend();
    backend.addListener(changed);
    if (widget.backend == null) backend.initialize();
    for (final c in [disc1, disc2, dlc]) {
      c.addListener(() {
        checked = false;
      });
    }
    Desktop.channel.setMethodCallHandler((call) async {
      if (call.method == 'closeRequested') {
        if (backend.busy) {
          await cancel(closeAfter: true);
        } else {
          await Desktop.close();
        }
      }
    });
  }

  void changed() {
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    backend.removeListener(changed);
    for (final c in [disc1, disc2, dlc, output]) {
      c.dispose();
    }
    if (widget.backend == null) backend.dispose();
    super.dispose();
  }

  void notice(String text) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
  Future<void> pick(
    TextEditingController target,
    bool directory,
    String title,
  ) async {
    try {
      final path = await Desktop.pick(directory: directory, title: title);
      if (path != null && mounted) {
        target.text = target == output ? '$path\\MagnaCarta2_CN' : path;
        setState(() {});
      }
    } catch (e) {
      if (mounted) notice('文件选择失败：$e');
    }
  }

  Map<String, dynamic> request(String operation) => {
    'operation': operation,
    'disc1': disc1.text.trim(),
    'disc2': disc2.text.trim(),
    'dlc': dlc.text.trim(),
    'include_dlc': includeDlc,
    'format': format,
    'output': output.text.trim(),
  };
  Future<void> inspect() async {
    setState(() => showErrors = true);
    if (!(form.currentState?.validate() ?? false)) return;
    await Desktop.busy(true);
    final ok = await backend.run(request('inspect'));
    await Desktop.busy(false);
    if (ok && mounted) {
      setState(() {
        checked = true;
        step = 1;
      });
    }
  }

  Future<void> install() async {
    if (!(form.currentState?.validate() ?? false)) return;
    if (!checked) {
      setState(() => step = 0);
      return;
    }
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        icon: const Icon(Icons.task_alt),
        title: const Text('开始生成汉化版本？'),
        content: Text(
          '输出格式：${format.toUpperCase()}\n${includeDlc ? "包含：双碟本体 + 两份汉化 DLC" : "仅包含双碟本体"}\n\n${output.text}\n\n原版文件只读。完成前不会创建最终输出目录。',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('返回检查'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('开始安装'),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted) return;
    setState(() => step = 2);
    await Desktop.busy(true);
    await backend.run(request('install'));
    await Desktop.busy(false);
    if (mounted) setState(() => step = 3);
  }

  Future<void> cancel({bool closeAfter = false}) async {
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('取消当前任务？'),
        content: const Text('会停止处理并清理本次临时文件，原版镜像与 DLC 不受影响。日志会保留。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('继续处理'),
          ),
          FilledButton.tonal(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('取消任务'),
          ),
        ],
      ),
    );
    if (accepted == true) {
      backend.cancel();
      if (closeAfter) {
        while (backend.busy) {
          await Future<void>.delayed(const Duration(milliseconds: 100));
        }
        await Desktop.close();
      }
    }
  }

  Future<void> open(String path) async {
    try {
      await Desktop.open(path);
    } catch (e) {
      if (mounted) notice('打开失败：$e');
    }
  }

  Future<void> exportLog() async {
    if (backend.logPath.isEmpty) {
      notice('安装开始后会生成完整日志。');
      return;
    }
    final directory = await Desktop.pick(directory: true, title: '选择日志导出目录');
    if (directory == null) return;
    final target = File(
      '$directory\\MC2-${DateTime.now().millisecondsSinceEpoch}.jsonl',
    );
    await File(backend.logPath).copy(target.path);
    if (mounted) notice('日志已导出：${target.path}');
  }

  Future<void> recover() async {
    if (output.text.trim().isEmpty) {
      notice('请先填写上次安装使用的最终输出路径。');
      return;
    }
    final accepted = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('清理已中断的安装？'),
        content: Text(
          '仅清理与下列输出路径及当前补丁身份匹配、且进程已结束的临时目录。原件、成功输出和日志保留。\n\n${output.text}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('返回'),
          ),
          FilledButton.tonal(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('核验并清理'),
          ),
        ],
      ),
    );
    if (accepted != true) return;
    await Desktop.busy(true);
    final ok = await backend.run(request('recover'));
    await Desktop.busy(false);
    if (mounted) notice(ok ? backend.message : backend.error);
  }

  void help() => showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: const Text('输入与兼容性说明'),
      content: const SizedBox(
        width: 620,
        child: SingleChildScrollView(
          child: Text(
            '支持韩版原版 Disc 1 / Disc 2。安装时检查完整 SHA256、Title ID、Media ID、盘号和全部资源。\n\n'
            'DLC 需要原版短剧包与特殊武器包。选择两个包所在的 00000002 文件夹；默认一起汉化输出。\n\n'
            'ZAR 推荐支持 ZArchive 的 Xenia Canary / Edge；XEX 推荐 RGH / JTAG，也兼容 Xenia。\n\n'
            'DLC 输出到标准 Content 目录，不塞进主游戏 ZAR。请使用模拟器的“安装内容”功能，或按输出说明复制到实际 content_root；实机复制到 HDD1:/Content/。\n\n'
            '完成后打开输出文件夹中的“使用说明.txt”，按所选格式启动游戏、安装 DLC 和换碟。请保留原存档备份；换碟和 RGH/JTAG 仍需实机确认。',
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => open(
            '${File(Platform.resolvedExecutable).parent.path}\\THIRD-PARTY',
          ),
          child: const Text('组件许可与源码'),
        ),
        FilledButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('明白了'),
        ),
      ],
    ),
  );
  Widget pathField(
    String label,
    String hint,
    TextEditingController controller, {
    bool directory = false,
    bool required = true,
    IconData icon = Icons.disc_full_outlined,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: TextFormField(
      controller: controller,
      enabled: !backend.busy,
      autovalidateMode: showErrors
          ? AutovalidateMode.onUserInteraction
          : AutovalidateMode.disabled,
      validator: (s) =>
          required && (s == null || s.trim().isEmpty) ? '请选择$label' : null,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        prefixIcon: Icon(icon),
        suffixIcon: Padding(
          padding: const EdgeInsets.all(6),
          child: IconButton.filledTonal(
            tooltip: '浏览$label',
            onPressed: backend.busy
                ? null
                : () => pick(controller, directory, label),
            icon: const Icon(Icons.folder_open),
          ),
        ),
      ),
    ),
  );
  Widget title(String eyebrow, String heading, String description) => Padding(
    padding: const EdgeInsets.only(bottom: 24),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow,
          style: TextStyle(
            color: Theme.of(context).colorScheme.primary,
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 1.4,
          ),
        ),
        const SizedBox(height: 8),
        Text(heading, style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 8),
        Text(
          description,
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
            height: 1.6,
          ),
        ),
      ],
    ),
  );
  Widget banner(IconData icon, String text, {bool error = false}) {
    final c = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: error ? c.errorContainer : c.secondaryContainer,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            size: 20,
            color: error ? c.onErrorContainer : c.onSecondaryContainer,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: SelectableText(
              text,
              style: TextStyle(
                color: error ? c.onErrorContainer : c.onSecondaryContainer,
                height: 1.55,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget sourcesPage() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      title('01 / 原版文件', '从你的韩版双碟开始', '选择原始 ISO。版本按内容识别，不依赖文件名。'),
      pathField('Disc 1 ISO', '选择第一张韩版原版镜像', disc1),
      pathField('Disc 2 ISO', '选择第二张韩版原版镜像', disc2),
      SwitchListTile.adaptive(
        contentPadding: EdgeInsets.zero,
        title: const Text('同时汉化 DLC'),
        subtitle: const Text('短剧包（3 集）与特殊武器包（12 种）'),
        value: includeDlc,
        onChanged: backend.busy
            ? null
            : (v) => setState(() {
                includeDlc = v;
                checked = false;
              }),
      ),
      AnimatedSize(
        duration: motion,
        curve: Curves.easeInOutCubic,
        child: includeDlc
            ? Padding(
                padding: const EdgeInsets.only(top: 12),
                child: pathField(
                  '原版 DLC 文件夹',
                  '选择包含两个 LIVE 包的 00000002 文件夹',
                  dlc,
                  directory: true,
                  icon: Icons.extension_outlined,
                ),
              )
            : const SizedBox.shrink(),
      ),
      if (backend.busy)
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: LinearProgressIndicator(
            value: backend.progress > 0 ? backend.progress : null,
          ),
        ),
      if (backend.error.isNotEmpty)
        banner(Icons.error_outline, backend.error, error: true),
    ],
  );
  Widget settingsPage() {
    final size =
        (backend.info?[format == 'zar' ? 'required_zar' : 'required_xex']
                as num? ??
            0) /
        1073741824;
    final c = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        title('02 / 输出设置', '选择你的游玩方式', '同一套汉化资源，两种输出结构。双碟始终独立保留。'),
        SizedBox(
          width: double.infinity,
          child: SegmentedButton<String>(
            segments: const [
              ButtonSegment(
                value: 'zar',
                label: Text('ZAR · Xenia'),
                icon: Icon(Icons.inventory_2_outlined),
              ),
              ButtonSegment(
                value: 'xex',
                label: Text('XEX · 实机 / Xenia'),
                icon: Icon(Icons.folder_copy_outlined),
              ),
            ],
            selected: {format},
            onSelectionChanged: (v) => setState(() => format = v.first),
            style: SegmentedButton.styleFrom(
              padding: const EdgeInsets.symmetric(vertical: 20),
            ),
          ),
        ),
        const SizedBox(height: 16),
        AnimatedSwitcher(
          duration: motion,
          child: Container(
            key: ValueKey(format),
            width: double.infinity,
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: c.surfaceContainerHigh,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              format == 'zar'
                  ? '推荐 Xenia Canary / Edge\n输出两份真正的 ZArchive，压缩后逐文件重新读取验证。'
                  : '推荐 Xbox 360 RGH / JTAG\n输出 Disc1 / Disc2 两套完整 XEX 文件树，也可在 Xenia 中打开。',
              style: const TextStyle(height: 1.8),
            ),
          ),
        ),
        const SizedBox(height: 24),
        pathField(
          '最终输出目录',
          '浏览上级目录，或输入一个全新路径',
          output,
          directory: true,
          icon: Icons.drive_folder_upload_outlined,
        ),
        Align(
          alignment: Alignment.centerRight,
          child: TextButton.icon(
            onPressed: backend.busy ? null : recover,
            icon: const Icon(Icons.restart_alt, size: 18),
            label: const Text('清理上次中断任务'),
          ),
        ),
        Row(
          children: [
            Icon(Icons.storage_outlined, size: 18, color: c.onSurfaceVariant),
            const SizedBox(width: 10),
            Text(
              '保守空间预算 ${size.toStringAsFixed(1)} GiB',
              style: TextStyle(color: c.onSurfaceVariant),
            ),
            const Spacer(),
            const Icon(Icons.verified_outlined, size: 18),
            const SizedBox(width: 6),
            const Text('原版文件只读'),
          ],
        ),
        const SizedBox(height: 20),
        banner(
          Icons.extension_outlined,
          includeDlc
              ? 'DLC 会一起生成到标准 Content 目录。Xenia 使用“安装内容”或复制到实际 content_root；实机复制到 HDD1:/Content/。'
              : '本次仅生成双碟本体，不包含 DLC。',
        ),
      ],
    );
  }

  Duration get motion => MediaQuery.of(context).disableAnimations
      ? Duration.zero
      : const Duration(milliseconds: 280);
  Widget processPage() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      title('03 / 安装过程', '正在构建你的汉化版本', '校验 → 提取与补丁 → DLC → 输出 → 完整读回'),
      const SizedBox(height: 20),
      Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            '${(backend.progress * 100).floor()}%',
            style: Theme.of(context).textTheme.displayMedium,
          ),
          const SizedBox(width: 16),
          Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Text(backend.cancelling ? '正在清理' : '请保持安装器运行'),
          ),
        ],
      ),
      const SizedBox(height: 24),
      TweenAnimationBuilder<double>(
        tween: Tween(end: backend.progress),
        duration: motion,
        builder: (context, value, _) => LinearProgressIndicator(
          value: value,
          minHeight: 8,
          borderRadius: BorderRadius.circular(8),
        ),
      ),
      const SizedBox(height: 20),
      Text(backend.message, style: Theme.of(context).textTheme.bodyLarge),
      const SizedBox(height: 28),
      logs(),
    ],
  );
  Widget resultPage() {
    final ok = backend.success, cancelled = backend.stage == 'cancelled';
    final c = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        AnimatedContainer(
          duration: motion,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: ok ? c.tertiaryContainer : c.errorContainer,
            shape: BoxShape.circle,
          ),
          child: Icon(
            ok
                ? Icons.check_rounded
                : cancelled
                ? Icons.stop_circle_outlined
                : Icons.error_outline,
            size: 40,
            color: ok ? c.onTertiaryContainer : c.onErrorContainer,
          ),
        ),
        const SizedBox(height: 20),
        title(
          '04 / 完成结果',
          ok
              ? '汉化文件已准备就绪'
              : cancelled
              ? '任务已取消'
              : '本次安装未完成',
          ok ? '全部文件已完成读回校验。现在可以按输出说明部署。' : '原版文件保持不变。请检查下面的信息后重试。',
        ),
        if (ok) ...[
          banner(Icons.folder_open, backend.output),
          const SizedBox(height: 16),
          Text(
            format == 'zar'
                ? '• MagnaCarta2_CN_Disc1.zar\n• MagnaCarta2_CN_Disc2.zar'
                : '• Disc1 / default.xex 与资源\n• Disc2 / default.xex 与资源',
            style: const TextStyle(height: 1.9),
          ),
          if (includeDlc)
            const Text('• Content / 两份已汉化 DLC', style: TextStyle(height: 1.9)),
          const Text('• 使用说明.txt · 安装结果.json', style: TextStyle(height: 1.9)),
          const SizedBox(height: 20),
          Wrap(
            spacing: 12,
            runSpacing: 12,
            children: [
              FilledButton.icon(
                onPressed: () => open(backend.output),
                icon: const Icon(Icons.folder_open),
                label: const Text('打开输出目录'),
              ),
              OutlinedButton.icon(
                onPressed: () => open('${backend.output}\\使用说明.txt'),
                icon: const Icon(Icons.menu_book_outlined),
                label: const Text('部署与换碟说明'),
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Text(
            '实际运行待验收：换碟、存档继承、DLC 识别与实机兼容。',
            style: TextStyle(fontSize: 12),
          ),
        ] else
          banner(
            cancelled ? Icons.info_outline : Icons.error_outline,
            backend.error.isNotEmpty ? backend.error : backend.message,
            error: !cancelled,
          ),
        const SizedBox(height: 24),
        logs(),
      ],
    );
  }

  Widget logs() {
    final filtered = backend.events
        .where((e) => logFilter == 'all' || e['level'] == logFilter)
        .toList();
    return Card.outlined(
      child: ExpansionTile(
        shape: const Border(),
        collapsedShape: const Border(),
        title: const Text('详细日志'),
        subtitle: Text('${backend.events.length} 条记录 · 完整日志独立保存'),
        leading: const Icon(Icons.receipt_long_outlined),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        children: [
          Row(
            children: [
              for (final (value, label) in [
                ('all', '全部'),
                ('warning', '警告'),
                ('error', '错误'),
              ])
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(label),
                    selected: logFilter == value,
                    onSelected: (_) => setState(() => logFilter = value),
                  ),
                ),
              const Spacer(),
              IconButton(
                tooltip: '导出日志',
                onPressed: exportLog,
                icon: const Icon(Icons.save_alt),
              ),
              IconButton(
                tooltip: '打开完整日志',
                onPressed: backend.logPath.isEmpty
                    ? null
                    : () => open(backend.logPath),
                icon: const Icon(Icons.open_in_new),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 190,
            child: SelectionArea(
              child: ListView.builder(
                itemCount: filtered.length,
                itemBuilder: (context, index) {
                  final e = filtered[index];
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 3),
                    child: Text(
                      '[${e['level'] ?? 'info'}] ${e['message'] ?? ''}',
                      style: TextStyle(
                        fontSize: 12,
                        height: 1.5,
                        color: e['level'] == 'error'
                            ? Theme.of(context).colorScheme.error
                            : null,
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final c = Theme.of(context).colorScheme;
    final labels = ['原版文件', '输出设置', '安装过程', '完成结果'];
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            SizedBox(
              width: double.infinity,
              height: 186,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    child: Semantics(
                      label: '真名法典 2 简体中文汉化补丁 LOGO',
                      image: true,
                      child: Image.asset(
                        'assets/logo.png',
                        height: 158,
                        fit: BoxFit.contain,
                        filterQuality: FilterQuality.high,
                      ),
                    ),
                  ),
                  Positioned(
                    left: 32,
                    top: 28,
                    child: Text(
                      'MAGNACARTA II\nLOCALIZATION',
                      style: TextStyle(
                        fontSize: 10,
                        letterSpacing: 2,
                        height: 1.8,
                        color: c.onSurfaceVariant,
                      ),
                    ),
                  ),
                  Positioned(
                    right: 24,
                    top: 20,
                    child: Row(
                      children: [
                        IconButton(
                          tooltip: widget.dark ? '切换浅色主题' : '切换深色主题',
                          onPressed: widget.onTheme,
                          icon: Icon(
                            widget.dark
                                ? Icons.light_mode_outlined
                                : Icons.dark_mode_outlined,
                          ),
                        ),
                        IconButton(
                          tooltip: '输入与兼容性说明',
                          onPressed: help,
                          icon: const Icon(Icons.help_outline),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(36, 0, 36, 22),
              child: Row(
                children: [
                  for (var i = 0; i < 4; i++) ...[
                    Expanded(
                      child: Semantics(
                        selected: step == i,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(16),
                          onTap: !backend.busy && i < 2 && (i == 0 || checked)
                              ? () => setState(() => step = i)
                              : null,
                          child: AnimatedContainer(
                            duration: motion,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 12,
                            ),
                            decoration: BoxDecoration(
                              color: step == i
                                  ? c.secondaryContainer
                                  : Colors.transparent,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                AnimatedContainer(
                                  duration: motion,
                                  width: 28,
                                  height: 28,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    color: step >= i
                                        ? c.primary
                                        : c.surfaceContainerHighest,
                                  ),
                                  alignment: Alignment.center,
                                  child: step > i
                                      ? Icon(
                                          Icons.check,
                                          size: 17,
                                          color: c.onPrimary,
                                        )
                                      : Text(
                                          '${i + 1}',
                                          style: TextStyle(
                                            color: step >= i
                                                ? c.onPrimary
                                                : c.onSurfaceVariant,
                                          ),
                                        ),
                                ),
                                const SizedBox(width: 10),
                                Text(
                                  labels[i],
                                  style: TextStyle(
                                    color: step == i
                                        ? c.onSecondaryContainer
                                        : c.onSurfaceVariant,
                                    fontWeight: step == i
                                        ? FontWeight.w600
                                        : FontWeight.normal,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                    if (i < 3)
                      SizedBox(
                        width: 42,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                          child: Divider(color: c.outlineVariant),
                        ),
                      ),
                  ],
                ],
              ),
            ),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 36),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 960),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(28),
                        child: Form(
                          key: form,
                          child: AnimatedSwitcher(
                            duration: motion,
                            switchInCurve: Curves.easeOutCubic,
                            switchOutCurve: Curves.easeInCubic,
                            transitionBuilder: (child, animation) =>
                                FadeTransition(
                                  opacity: animation,
                                  child: SlideTransition(
                                    position: Tween(
                                      begin: const Offset(.025, 0),
                                      end: Offset.zero,
                                    ).animate(animation),
                                    child: child,
                                  ),
                                ),
                            child: KeyedSubtree(
                              key: ValueKey(step),
                              child: switch (step) {
                                0 => sourcesPage(),
                                1 => settingsPage(),
                                2 => processPage(),
                                _ => resultPage(),
                              },
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(36, 20, 36, 12),
              child: Row(
                children: [
                  if (step == 1)
                    OutlinedButton.icon(
                      onPressed: backend.busy
                          ? null
                          : () => setState(() => step = 0),
                      icon: const Icon(Icons.arrow_back),
                      label: const Text('上一步'),
                    ),
                  if (step == 3)
                    OutlinedButton.icon(
                      onPressed: () => setState(() => step = 1),
                      icon: const Icon(Icons.refresh),
                      label: const Text('返回设置'),
                    ),
                  if (backend.loading)
                    const Row(
                      children: [
                        SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                        SizedBox(width: 12),
                        Text('正在校验安装组件'),
                      ],
                    ),
                  if (!backend.loading && step < 2)
                    Text(
                      step == 0 ? '双碟独立 · 源文件只读' : '  校验完成后才发布输出',
                      style: TextStyle(fontSize: 12, color: c.onSurfaceVariant),
                    ),
                  const Spacer(),
                  if (backend.busy)
                    OutlinedButton.icon(
                      onPressed: backend.cancelling ? null : cancel,
                      icon: const Icon(Icons.close),
                      label: Text(backend.cancelling ? '正在取消' : '取消任务'),
                    ),
                  if (step == 0 && !backend.busy)
                    FilledButton.icon(
                      onPressed: backend.loading || backend.info == null
                          ? null
                          : inspect,
                      icon: const Icon(Icons.arrow_forward),
                      label: const Text('检查文件并继续'),
                    ),
                  if (step == 1 && !backend.busy)
                    FilledButton.icon(
                      onPressed: install,
                      icon: const Icon(Icons.auto_fix_high_outlined),
                      label: const Text('开始安装'),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(36, 0, 16, 6),
              child: Row(
                children: [
                  Text(
                    '《真名法典2》简体中文汉化补丁  ·  ${backend.info?['version'] ?? 'v1.0'}',
                    style: TextStyle(color: c.onSurfaceVariant, fontSize: 11),
                  ),
                  const Spacer(),
                  TextButton(
                    onPressed: () async {
                      try {
                        await Desktop.blog();
                      } catch (e) {
                        if (mounted) notice('链接打开失败：$e');
                      }
                    },
                    child: const Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('伯翎飞云'),
                        SizedBox(width: 5),
                        Icon(Icons.open_in_new, size: 13),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
