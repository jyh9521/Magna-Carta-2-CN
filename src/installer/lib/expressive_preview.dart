// Throwaway desktop UI study: A split canvas, B editorial wizard, C workbench.
// Independent entry point; installation/progress/results are in-memory demos.
// --variant=A|B|C selects the layout. The production entry point is untouched.
import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/physics.dart';
import 'package:flutter/services.dart';

import 'desktop.dart';

void main(List<String> args) {
  WidgetsFlutterBinding.ensureInitialized();
  final option = args.where((a) => a.startsWith('--variant=')).firstOrNull;
  runApp(
    ExpressivePreviewApp(
      initialVariant:
          option?.split('=').last ?? Uri.base.queryParameters['variant'] ?? 'A',
      initialDark: args.contains('--dark'),
    ),
  );
}

class ExpressivePreviewApp extends StatefulWidget {
  const ExpressivePreviewApp({
    super.key,
    this.initialVariant = 'A',
    this.initialDark = false,
    this.demoTick = const Duration(milliseconds: 70),
  });
  final String initialVariant;
  final bool initialDark;
  final Duration demoTick;
  @override
  State<ExpressivePreviewApp> createState() => _ExpressivePreviewAppState();
}

class _ExpressivePreviewAppState extends State<ExpressivePreviewApp> {
  late bool dark = widget.initialDark;
  late String variant = ['A', 'B', 'C'].contains(widget.initialVariant)
      ? widget.initialVariant
      : 'A';
  @override
  Widget build(BuildContext context) {
    final seed = switch (variant) {
      'B' => const Color(0xff994636),
      'C' => const Color(0xff006b65),
      _ => const Color(0xff7055ad),
    };
    ThemeData theme(Brightness brightness) {
      final c = ColorScheme.fromSeed(seedColor: seed, brightness: brightness);
      return ThemeData(
        useMaterial3: true,
        colorScheme: c,
        fontFamily: 'Microsoft YaHei UI',
        scaffoldBackgroundColor: c.surface,
        visualDensity: VisualDensity.standard,
        textTheme: TextTheme(
          headlineLarge: TextStyle(
            fontSize: 32,
            height: 1.3,
            fontWeight: FontWeight.w700,
            color: c.onSurface,
          ),
          titleLarge: const TextStyle(
            fontSize: 20,
            height: 1.4,
            fontWeight: FontWeight.w700,
          ),
          bodyMedium: const TextStyle(fontSize: 13, height: 1.6),
          labelLarge: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            minimumSize: const Size(156, 56),
            padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 18),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: c.surfaceContainerHighest,
          border: OutlineInputBorder(
            borderSide: BorderSide.none,
            borderRadius: BorderRadius.circular(18),
          ),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 18,
            vertical: 20,
          ),
        ),
        snackBarTheme: SnackBarThemeData(
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
          ),
        ),
        tooltipTheme: const TooltipThemeData(
          waitDuration: Duration(milliseconds: 400),
        ),
      );
    }

    return MaterialApp(
      title: '真名法典2 · Material 3 Expressive 预览',
      debugShowCheckedModeBanner: false,
      theme: theme(Brightness.light),
      darkTheme: theme(Brightness.dark),
      themeMode: dark ? ThemeMode.dark : ThemeMode.light,
      themeAnimationDuration: const Duration(milliseconds: 350),
      home: _PreviewHome(
        variant: variant,
        dark: dark,
        demoTick: widget.demoTick,
        onTheme: () => setState(() => dark = !dark),
        onVariant: (value) => setState(() => variant = value),
      ),
    );
  }
}

class _PreviewHome extends StatefulWidget {
  const _PreviewHome({
    required this.variant,
    required this.dark,
    required this.onTheme,
    required this.onVariant,
    required this.demoTick,
  });
  final String variant;
  final bool dark;
  final VoidCallback onTheme;
  final ValueChanged<String> onVariant;
  final Duration demoTick;
  @override
  State<_PreviewHome> createState() => _PreviewHomeState();
}

class _PreviewHomeState extends State<_PreviewHome>
    with SingleTickerProviderStateMixin {
  final disc1 = TextEditingController(),
      disc2 = TextEditingController(),
      dlc = TextEditingController();
  final output = TextEditingController(text: r'D:\Games\MagnaCarta2_CN');
  final scroll = ScrollController();
  late final spring = AnimationController.unbounded(vsync: this, value: 1);
  Timer? timer;
  int step = 0;
  double progress = 0;
  bool includeDlc = true, error = false, stopped = false;
  String format = 'ZAR';
  String? message;
  static const stages = ['原版文件', '输出设置', '安装过程', '完成结果'];
  static const names = {'A': '紫藤分栏', 'B': '赤陶向导', 'C': '青瓷工作台'};
  ColorScheme get c => Theme.of(context).colorScheme;
  TextTheme get t => Theme.of(context).textTheme;

  @override
  void dispose() {
    timer?.cancel();
    spring.dispose();
    scroll.dispose();
    for (final controller in [disc1, disc2, dlc, output]) {
      controller.dispose();
    }
    super.dispose();
  }

  void notify(String value) => setState(() => message = value);
  void go(int value) {
    timer?.cancel();
    setState(() {
      step = value;
      error = false;
      stopped = false;
      message = null;
    });
    if (scroll.hasClients) scroll.jumpTo(0);
    if (!MediaQuery.disableAnimationsOf(context)) {
      spring.value = .92;
      spring.animateWith(
        SpringSimulation(
          const SpringDescription(mass: 1, stiffness: 220, damping: 22),
          .92,
          1,
          0,
        ),
      );
    }
  }

  void cycle(int delta) {
    final values = names.keys.toList();
    widget.onVariant(
      values[(values.indexOf(widget.variant) + delta) % values.length],
    );
  }

  void samples() {
    setState(() {
      disc1.text = 'MagnaCarta II (Korea) (Disc 1).iso';
      disc2.text = 'MagnaCarta II (Korea) (Disc 2).iso';
      dlc.text = r'D:\Originals\4E4D0811\00000002';
    });
  }

  Future<void> pick(
    TextEditingController controller, {
    bool directory = false,
  }) async {
    try {
      final value = await Desktop.pick(
        directory: directory,
        title: '预览：选择${directory ? '文件夹' : 'ISO'}（仅显示路径）',
      );
      if (mounted && value != null) setState(() => controller.text = value);
    } catch (_) {
      if (mounted) notify('文件对话框未返回路径，可使用演示文件体验');
    }
  }

  void next() {
    if (step == 0) {
      if (disc1.text.trim().isEmpty ||
          disc2.text.trim().isEmpty ||
          (includeDlc && dlc.text.trim().isEmpty)) {
        notify('请先选择双盘文件和 DLC，或点击「填入演示文件」');
        return;
      }
      go(1);
    } else if (step == 1) {
      if (output.text.trim().isEmpty) {
        notify('请填写演示输出路径');
        return;
      }
      go(2);
      startDemo();
    } else if (step == 3) {
      go(0);
    }
  }

  void startDemo() {
    timer?.cancel();
    setState(() {
      progress = 0;
      error = false;
      stopped = false;
    });
    timer = Timer.periodic(widget.demoTick, (tick) {
      if (!mounted) {
        tick.cancel();
        return;
      }
      setState(() => progress = math.min(1, progress + .014));
      if (progress >= 1) {
        tick.cancel();
        go(3);
      }
    });
  }

  Widget label(String text, {Color? color}) => Text(
    text,
    style: TextStyle(
      fontSize: 11,
      fontWeight: FontWeight.w700,
      letterSpacing: 1.8,
      color: color ?? c.primary,
    ),
  );
  Widget badge(String text, {IconData icon = Icons.science_outlined}) =>
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
        decoration: BoxDecoration(
          color: c.secondaryContainer,
          borderRadius: BorderRadius.circular(30),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 15, color: c.onSecondaryContainer),
            const SizedBox(width: 7),
            Text(
              text,
              style: TextStyle(
                fontSize: 11,
                color: c.onSecondaryContainer,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      );

  @override
  Widget build(BuildContext context) => Focus(
    onKeyEvent: (_, event) {
      final focus = FocusManager.instance.primaryFocus?.context;
      final editing =
          focus?.findAncestorWidgetOfExactType<EditableText>() != null;
      if (event is KeyDownEvent && !editing) {
        if (event.logicalKey == LogicalKeyboardKey.arrowRight) {
          cycle(1);
          return KeyEventResult.handled;
        }
        if (event.logicalKey == LogicalKeyboardKey.arrowLeft) {
          cycle(-1);
          return KeyEventResult.handled;
        }
      }
      return KeyEventResult.ignored;
    },
    child: Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 12),
          child: Column(
            children: [
              header(),
              if (message != null)
                Container(
                  margin: const EdgeInsets.only(top: 10),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: c.tertiaryContainer,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.info_outline_rounded,
                        size: 18,
                        color: c.onTertiaryContainer,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          message!,
                          style: TextStyle(
                            fontSize: 12,
                            color: c.onTertiaryContainer,
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: '关闭提示',
                        onPressed: () => setState(() => message = null),
                        icon: const Icon(Icons.close_rounded, size: 18),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 20),
              Expanded(
                child: LayoutBuilder(
                  builder: (context, bounds) {
                    if (bounds.maxWidth < 800) return compactLayout();
                    return switch (widget.variant) {
                      'B' => editorialLayout(),
                      'C' => workbenchLayout(),
                      _ => splitLayout(),
                    };
                  },
                ),
              ),
              const SizedBox(height: 12),
              footer(),
            ],
          ),
        ),
      ),
    ),
  );

  Widget header() => Row(
    children: [
      Image.asset(
        'assets/logo.png',
        width: 150,
        height: 42,
        fit: BoxFit.contain,
      ),
      const SizedBox(width: 18),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '真名法典 2',
              style: t.titleMedium?.copyWith(fontWeight: FontWeight.w700),
            ),
            Text(
              '简体中文汉化补丁  /  UI DESIGN STUDY',
              style: TextStyle(
                fontSize: 10,
                letterSpacing: 1,
                color: c.onSurfaceVariant,
              ),
            ),
          ],
        ),
      ),
      badge('设计预览'),
      const SizedBox(width: 10),
      IconButton.filledTonal(
        key: const Key('theme'),
        tooltip: widget.dark ? '切换浅色主题' : '切换深色主题',
        onPressed: widget.onTheme,
        icon: Icon(
          widget.dark ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
        ),
      ),
      const SizedBox(width: 6),
      IconButton(
        tooltip: '关于预览',
        onPressed: () => showDialog<void>(
          context: context,
          builder: (context) => AlertDialog(
            icon: const Icon(Icons.auto_awesome_outlined),
            title: const Text('先感受界面，再决定风格'),
            content: const Text(
              '这是独立的 Material 3 Expressive 设计预览。\n\nA 紫藤分栏 · B 赤陶向导 · C 青瓷工作台\n底部箭头或键盘 ← → 切换布局，右上角切换主题。\n\n路径仅用于界面展示；进度、错误与结果均为演示，不执行校验、安装或写入。现有安装器保持原样。',
            ),
            actions: [
              FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('开始体验'),
              ),
            ],
          ),
        ),
        icon: const Icon(Icons.help_outline_rounded),
      ),
    ],
  );

  // A: asymmetric brand canvas beside a focused task surface.
  Widget splitLayout() => Row(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      SizedBox(
        width: 284,
        child: Container(
          padding: const EdgeInsets.all(26),
          decoration: BoxDecoration(
            color: c.primaryContainer,
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(32),
              topRight: Radius.circular(64),
              bottomLeft: Radius.circular(32),
              bottomRight: Radius.circular(32),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              label('A NEW WAY TO ADVENTURE', color: c.onPrimaryContainer),
              const SizedBox(height: 24),
              Text(
                '让冒险，\n用中文继续。',
                style: TextStyle(
                  fontSize: 34,
                  height: 1.38,
                  fontWeight: FontWeight.w800,
                  color: c.onPrimaryContainer,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                '熟悉的世界，全新的表达。',
                style: TextStyle(color: c.onPrimaryContainer, fontSize: 12),
              ),
              Expanded(
                child: Center(child: FittedBox(child: expressiveMark(174))),
              ),
              ...List.generate(
                4,
                (i) => Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: stageTile(i),
                ),
              ),
              const SizedBox(height: 12),
              Text(
                '双盘独立 · 原版保留',
                style: TextStyle(
                  color: c.onPrimaryContainer,
                  fontSize: 10,
                  letterSpacing: 1,
                ),
              ),
            ],
          ),
        ),
      ),
      const SizedBox(width: 24),
      Expanded(child: taskSurface()),
    ],
  );

  // B: editorial masthead and horizontal steps, without a side navigation pane.
  Widget editorialLayout() => Column(
    children: [
      Container(
        padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 18),
        decoration: BoxDecoration(
          color: c.primary,
          borderRadius: BorderRadius.circular(36),
        ),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  label('MAGNACARTA II / LOCALIZATION', color: c.onPrimary),
                  const SizedBox(height: 8),
                  Text(
                    '下一段旅程，从这里开始。',
                    style: TextStyle(
                      fontSize: 30,
                      height: 1.3,
                      fontWeight: FontWeight.w800,
                      color: c.onPrimary,
                    ),
                  ),
                ],
              ),
            ),
            expressiveMark(95, tonal: true),
          ],
        ),
      ),
      const SizedBox(height: 12),
      Row(
        children: List.generate(
          4,
          (i) => Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: stageTile(i, horizontal: true),
            ),
          ),
        ),
      ),
      const SizedBox(height: 14),
      Expanded(child: taskSurface(compact: true)),
    ],
  );

  // C: compact icon rail, working canvas, persistent contextual summary.
  Widget workbenchLayout() => Row(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Container(
        width: 74,
        padding: const EdgeInsets.symmetric(vertical: 20),
        decoration: BoxDecoration(
          color: c.secondaryContainer,
          borderRadius: BorderRadius.circular(32),
        ),
        child: Column(
          children: [
            Icon(Icons.auto_awesome_rounded, color: c.onSecondaryContainer),
            const SizedBox(height: 30),
            ...List.generate(
              4,
              (i) => Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Tooltip(
                  message: stages[i],
                  child: stageTile(i, iconOnly: true),
                ),
              ),
            ),
            const Spacer(),
            Icon(
              Icons.lock_outline_rounded,
              color: c.onSecondaryContainer,
              size: 18,
            ),
          ],
        ),
      ),
      const SizedBox(width: 20),
      Expanded(child: taskSurface(compact: true)),
      const SizedBox(width: 20),
      Container(
        width: 214,
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: c.primaryContainer,
          borderRadius: BorderRadius.circular(32),
        ),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              label('SESSION / PREVIEW', color: c.onPrimaryContainer),
              const SizedBox(height: 26),
              Text(
                '旅程清单',
                style: t.titleLarge?.copyWith(color: c.onPrimaryContainer),
              ),
              const SizedBox(height: 24),
              summaryLine('语言', '简体中文'),
              summaryLine('游戏版本', 'Korea · 双盘'),
              summaryLine('输出格式', format),
              summaryLine('附加内容', includeDlc ? '包含 DLC' : '仅本体'),
              const SizedBox(height: 12),
              expressiveMark(120),
              const SizedBox(height: 22),
              Text(
                '这里的每一步，\n都只是一次设计预演。',
                style: TextStyle(
                  fontSize: 12,
                  height: 1.8,
                  color: c.onPrimaryContainer,
                ),
              ),
            ],
          ),
        ),
      ),
    ],
  );

  Widget compactLayout() => Column(
    children: [
      Row(
        children: List.generate(
          4,
          (i) => Expanded(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 3),
              child: stageTile(i, horizontal: true),
            ),
          ),
        ),
      ),
      const SizedBox(height: 16),
      Expanded(child: taskSurface(compact: true)),
    ],
  );

  Widget summaryLine(String name, String value) => Padding(
    padding: const EdgeInsets.only(bottom: 22),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(name, style: TextStyle(fontSize: 11, color: c.onPrimaryContainer)),
        const SizedBox(height: 3),
        Text(
          value,
          style: TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: c.onPrimaryContainer,
          ),
        ),
      ],
    ),
  );

  Widget stageTile(
    int index, {
    bool horizontal = false,
    bool iconOnly = false,
  }) {
    final active = step == index, complete = step > index;
    final icons = [
      Icons.folder_open_rounded,
      Icons.tune_rounded,
      Icons.auto_awesome_rounded,
      Icons.check_rounded,
    ];
    return Semantics(
      selected: active,
      label: '${index + 1} ${stages[index]}',
      child: AnimatedContainer(
        key: Key('stage-$index'),
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOutCubic,
        decoration: BoxDecoration(
          color: active ? c.primary : Colors.transparent,
          borderRadius: BorderRadius.circular(active ? 22 : 12),
        ),
        padding: EdgeInsets.symmetric(
          horizontal: 14,
          vertical: horizontal ? 12 : 10,
        ),
        child: Row(
          mainAxisSize: iconOnly ? MainAxisSize.min : MainAxisSize.max,
          children: [
            Icon(
              complete ? Icons.check_circle_rounded : icons[index],
              size: 20,
              color: active ? c.onPrimary : c.onSurfaceVariant,
            ),
            if (!iconOnly) ...[
              const SizedBox(width: 12),
              Flexible(
                child: Text(
                  stages[index],
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                    color: active ? c.onPrimary : c.onSurfaceVariant,
                  ),
                ),
              ),
              if (!horizontal) ...[
                const Spacer(),
                Text(
                  '0${index + 1}',
                  style: TextStyle(
                    fontSize: 10,
                    color: active ? c.onPrimary : c.onSurfaceVariant,
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  Widget taskSurface({bool compact = false}) => Container(
    padding: EdgeInsets.all(compact ? 22 : 26),
    decoration: BoxDecoration(
      color: c.surfaceContainerLow,
      borderRadius: BorderRadius.circular(32),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          child: SingleChildScrollView(
            controller: scroll,
            child: AnimatedBuilder(
              animation: spring,
              builder: (context, child) => Transform.scale(
                scale: spring.value.clamp(.85, 1.06),
                alignment: Alignment.topCenter,
                child: child,
              ),
              child: AnimatedSwitcher(
                duration: MediaQuery.disableAnimationsOf(context)
                    ? Duration.zero
                    : const Duration(milliseconds: 280),
                switchInCurve: Curves.easeOutCubic,
                switchOutCurve: Curves.easeInCubic,
                child: SizedBox(
                  key: ValueKey(step),
                  width: double.infinity,
                  child: switch (step) {
                    1 => settingsPage(),
                    2 => progressPage(),
                    3 => resultPage(),
                    _ => sourcePage(),
                  },
                ),
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            if (step == 0)
              Expanded(
                child: TextButton.icon(
                  key: const Key('samples'),
                  onPressed: samples,
                  icon: const Icon(Icons.play_circle_outline_rounded, size: 19),
                  label: const Text('填入演示文件'),
                ),
              )
            else
              Expanded(
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: TextButton.icon(
                    key: const Key('back'),
                    onPressed: step == 2
                        ? () {
                            go(1);
                            setState(() => stopped = true);
                          }
                        : () => go(0),
                    icon: Icon(
                      step == 2
                          ? Icons.close_rounded
                          : Icons.arrow_back_rounded,
                      size: 18,
                    ),
                    label: Text(
                      step == 2
                          ? '取消演示'
                          : step == 3
                          ? '重新体验'
                          : '上一步',
                    ),
                  ),
                ),
              ),
            if (step != 2)
              FilledButton.icon(
                key: const Key('next'),
                onPressed: next,
                iconAlignment: IconAlignment.end,
                icon: Icon(
                  step == 3
                      ? Icons.replay_rounded
                      : Icons.arrow_forward_rounded,
                  size: 20,
                ),
                label: Text(
                  step == 0
                      ? '继续'
                      : step == 1
                      ? '预览安装'
                      : '返回开始',
                ),
              ),
          ],
        ),
      ],
    ),
  );

  Widget pageHeading(String title, String subtitle) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      label(
        '0${step + 1} / 04   ·   ${step == 0
            ? 'SOURCE FILES'
            : step == 1
            ? 'MAKE IT YOURS'
            : step == 2
            ? 'A LITTLE MAGIC'
            : 'ALL SET'}',
      ),
      const SizedBox(height: 10),
      Text(title, style: t.headlineLarge),
      const SizedBox(height: 7),
      Text(
        subtitle,
        style: TextStyle(fontSize: 12, height: 1.7, color: c.onSurfaceVariant),
      ),
      const SizedBox(height: 24),
    ],
  );

  Widget sourcePage() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      pageHeading('准备好，开始新旅程', '选择韩版原盘，留住最初的冒险。\n这一次，我们用中文出发。'),
      fileTile('DISC 01', '第一盘镜像', disc1, keyName: 'disc1', number: '01'),
      const SizedBox(height: 10),
      fileTile('DISC 02', '第二盘镜像', disc2, keyName: 'disc2', number: '02'),
      const SizedBox(height: 18),
      Container(
        padding: const EdgeInsets.fromLTRB(18, 10, 12, 14),
        decoration: BoxDecoration(
          color: c.surfaceContainer,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Column(
          children: [
            Row(
              children: [
                Icon(Icons.extension_outlined, size: 21, color: c.primary),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('也带上额外的故事', style: t.labelLarge),
                      Text(
                        '包含两份 DLC 的汉化',
                        style: TextStyle(
                          fontSize: 11,
                          color: c.onSurfaceVariant,
                        ),
                      ),
                    ],
                  ),
                ),
                Switch(
                  key: const Key('dlc-toggle'),
                  value: includeDlc,
                  onChanged: (value) => setState(() => includeDlc = value),
                ),
              ],
            ),
            if (includeDlc) ...[
              const SizedBox(height: 7),
              InkWell(
                key: const Key('dlc-pick'),
                borderRadius: BorderRadius.circular(12),
                onTap: () => pick(dlc, directory: true),
                child: Padding(
                  padding: const EdgeInsets.all(8),
                  child: Row(
                    children: [
                      Icon(
                        Icons.folder_outlined,
                        color: c.onSurfaceVariant,
                        size: 18,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          dlc.text.isEmpty ? '选择原版 DLC 文件夹' : dlc.text,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 11,
                            color: c.onSurfaceVariant,
                          ),
                        ),
                      ),
                      const Icon(Icons.chevron_right_rounded, size: 18),
                    ],
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
      const SizedBox(height: 16),
      Row(
        children: [
          Icon(Icons.shield_outlined, size: 16, color: c.primary),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '原版保留  ·  双盘独立  ·  可选附加内容',
              style: TextStyle(fontSize: 10, color: c.onSurfaceVariant),
            ),
          ),
        ],
      ),
    ],
  );

  Widget fileTile(
    String tag,
    String title,
    TextEditingController controller, {
    required String keyName,
    required String number,
  }) {
    final selected = controller.text.isNotEmpty;
    return Material(
      color: selected ? c.secondaryContainer : c.surfaceContainerLowest,
      borderRadius: BorderRadius.circular(22),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        key: Key(keyName),
        onTap: () => pick(controller),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: selected ? c.primary : c.primaryContainer,
                  borderRadius: BorderRadius.circular(selected ? 25 : 16),
                ),
                alignment: Alignment.center,
                child: selected
                    ? Icon(Icons.check_rounded, color: c.onPrimary)
                    : Text(
                        number,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w800,
                          color: c.onPrimaryContainer,
                        ),
                      ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '$tag  /  $title',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: c.onSurface,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      selected ? controller.text : '点击选择 .iso 文件',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(fontSize: 11, color: c.onSurfaceVariant),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Icon(
                selected ? Icons.swap_horiz_rounded : Icons.add_rounded,
                color: c.primary,
                size: 23,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget settingsPage() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      pageHeading('按你的方式，出发', '选择游玩平台，设置中文版本的存放位置。'),
      if (stopped)
        Padding(
          padding: const EdgeInsets.only(bottom: 14),
          child: badge(
            '演示已取消 · 没有生成文件',
            icon: Icons.pause_circle_outline_rounded,
          ),
        ),
      Row(
        children: [
          Expanded(
            child: formatTile(
              'ZAR',
              'Xenia 模拟器',
              Icons.desktop_windows_rounded,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: formatTile(
              'XEX',
              '实机 / Xenia',
              Icons.sports_esports_rounded,
            ),
          ),
        ],
      ),
      const SizedBox(height: 22),
      Text('输出文件夹', style: t.labelLarge),
      const SizedBox(height: 10),
      TextField(
        key: const Key('output'),
        controller: output,
        onChanged: (_) => setState(() {}),
        decoration: InputDecoration(
          hintText: '填写一个新的输出位置',
          prefixIcon: const Icon(Icons.folder_outlined),
          suffixIcon: IconButton(
            tooltip: '选择演示输出位置',
            onPressed: () => pick(output, directory: true),
            icon: const Icon(Icons.more_horiz_rounded),
          ),
        ),
      ),
      const SizedBox(height: 20),
      Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: c.tertiaryContainer,
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              Icons.auto_awesome_outlined,
              color: c.onTertiaryContainer,
              size: 22,
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Text(
                format == 'ZAR'
                    ? '轻装出发\n双盘分别生成 ZArchive 容器，DLC 保持独立。'
                    : '自由部署\n双盘分别保留 XEX 目录结构，DLC 保持独立。',
                style: TextStyle(
                  fontSize: 12,
                  height: 1.8,
                  color: c.onTertiaryContainer,
                ),
              ),
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      Text(
        '当前为界面演示，不估算真实空间，也不创建此目录。',
        style: TextStyle(fontSize: 11, color: c.onSurfaceVariant),
      ),
    ],
  );

  Widget formatTile(String value, String subtitle, IconData icon) {
    final selected = format == value;
    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: selected ? c.primaryContainer : c.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(selected ? 30 : 20),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          key: Key('format-$value'),
          onTap: () => setState(() => format = value),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 280),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              border: Border.all(
                width: 2,
                color: selected ? c.primary : Colors.transparent,
              ),
              borderRadius: BorderRadius.circular(selected ? 30 : 20),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(icon, size: 27, color: c.primary),
                    const Spacer(),
                    if (selected)
                      Icon(
                        Icons.check_circle_rounded,
                        size: 20,
                        color: c.primary,
                      ),
                  ],
                ),
                const SizedBox(height: 16),
                Text(value, style: t.titleLarge),
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: TextStyle(fontSize: 11, color: c.onSurfaceVariant),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget progressPage() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      pageHeading(
        error ? '先停一下，检查文件' : '把中文，带进这个世界',
        error ? '这是错误状态的视觉演示，没有实际读取镜像。' : '演示正在进行。真实安装时，这里会显示实际处理阶段。',
      ),
      Center(
        child: expressiveMark(
          136,
          symbol: error ? '!' : '${(progress * 100).round()}',
        ),
      ),
      const SizedBox(height: 22),
      Text(
        error
            ? '演示：镜像摘要与支持版本不符'
            : progress < .25
            ? '演示 · 核对双盘身份'
            : progress < .75
            ? '演示 · 应用本地化资源'
            : '演示 · 读回与整理结果',
        textAlign: TextAlign.center,
        style: t.labelLarge,
      ),
      const SizedBox(height: 16),
      ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: LinearProgressIndicator(
          value: progress,
          minHeight: 12,
          color: error ? c.error : c.primary,
          backgroundColor: c.surfaceContainerHighest,
        ),
      ),
      const SizedBox(height: 22),
      Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          OutlinedButton.icon(
            key: const Key('error-demo'),
            onPressed: () {
              timer?.cancel();
              setState(() => error = true);
            },
            icon: const Icon(Icons.error_outline_rounded, size: 17),
            label: const Text('查看异常样式'),
          ),
          if (error) ...[
            const SizedBox(width: 12),
            FilledButton.tonal(
              key: const Key('retry'),
              onPressed: startDemo,
              child: const Text('重新演示'),
            ),
          ],
        ],
      ),
      const SizedBox(height: 20),
      Text(
        '演示不会运行安装后端；关闭窗口即可结束。',
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 11, color: c.onSurfaceVariant),
      ),
    ],
  );

  Widget resultPage() => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      pageHeading('准备就绪，去冒险吧', '这是完成页面的效果预览，尚未生成游戏文件。'),
      Center(child: expressiveMark(142, symbol: '✓')),
      const SizedBox(height: 20),
      Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          color: c.secondaryContainer,
          borderRadius: BorderRadius.circular(26),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.check_circle_outline_rounded,
                  color: c.onSecondaryContainer,
                  size: 19,
                ),
                const SizedBox(width: 10),
                Text(
                  '演示流程已完成',
                  style: TextStyle(
                    fontWeight: FontWeight.w700,
                    color: c.onSecondaryContainer,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            Text(
              '简体中文  /  $format  /  ${includeDlc ? '双盘 + DLC' : '双盘本体'}',
              style: TextStyle(fontSize: 12, color: c.onSecondaryContainer),
            ),
            const SizedBox(height: 8),
            Text(
              output.text,
              style: TextStyle(fontSize: 11, color: c.onSecondaryContainer),
            ),
          ],
        ),
      ),
      const SizedBox(height: 18),
      Text(
        '你可以切换布局、深浅主题，或重新走一遍流程。',
        textAlign: TextAlign.center,
        style: TextStyle(fontSize: 11, color: c.onSurfaceVariant),
      ),
    ],
  );

  Widget expressiveMark(
    double size, {
    String symbol = '文',
    bool tonal = false,
  }) => Semantics(
    excludeSemantics: true,
    child: SizedBox(
      width: size,
      height: size,
      child: CustomPaint(
        painter: _FlowerPainter(
          tonal ? c.primaryContainer : c.primary,
          c.tertiaryContainer,
        ),
        child: Center(
          child: Transform.rotate(
            angle: -.10,
            child: Text(
              symbol,
              style: TextStyle(
                fontSize: symbol.length > 1 ? size * .30 : size * .40,
                fontWeight: FontWeight.w800,
                height: 1,
                color: tonal ? c.onPrimaryContainer : c.onPrimary,
              ),
            ),
          ),
        ),
      ),
    ),
  );

  Widget footer() => Row(
    children: [
      Expanded(
        child: Text(
          'MATERIAL 3\nEXPRESSIVE',
          style: TextStyle(
            fontSize: 9,
            height: 1.5,
            letterSpacing: 2,
            fontWeight: FontWeight.w700,
            color: c.onSurfaceVariant,
          ),
        ),
      ),
      Container(
        decoration: BoxDecoration(
          color: c.inverseSurface,
          borderRadius: BorderRadius.circular(32),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              key: const Key('variant-prev'),
              tooltip: '上一个布局',
              onPressed: () => cycle(-1),
              icon: Icon(Icons.chevron_left_rounded, color: c.onInverseSurface),
            ),
            SizedBox(
              width: 162,
              child: Column(
                children: [
                  Text(
                    '布局 ${widget.variant} · ${names[widget.variant]}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: c.onInverseSurface,
                    ),
                  ),
                  Text(
                    '← → 切换  ·  状态 ${step + 1}/4',
                    style: TextStyle(fontSize: 9, color: c.onInverseSurface),
                  ),
                ],
              ),
            ),
            IconButton(
              key: const Key('variant-next'),
              tooltip: '下一个布局',
              onPressed: () => cycle(1),
              icon: Icon(
                Icons.chevron_right_rounded,
                color: c.onInverseSurface,
              ),
            ),
          ],
        ),
      ),
      Expanded(
        child: Align(
          alignment: Alignment.centerRight,
          child: TextButton(
            onPressed: () async {
              try {
                await Desktop.blog();
              } catch (_) {
                if (mounted) notify('https://blog.blfy.cc/');
              }
            },
            child: const Text('伯翎飞云', style: TextStyle(fontSize: 11)),
          ),
        ),
      ),
    ],
  );
}

class _FlowerPainter extends CustomPainter {
  const _FlowerPainter(this.color, this.accent);
  final Color color, accent;
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    Path flower(double radius, double phase) {
      final path = Path();
      for (var i = 0; i <= 240; i++) {
        final angle = i * math.pi * 2 / 240;
        final r = radius * (.88 + .12 * math.cos(10 * angle + phase));
        final p = center + Offset(math.cos(angle) * r, math.sin(angle) * r);
        if (i == 0) {
          path.moveTo(p.dx, p.dy);
        } else {
          path.lineTo(p.dx, p.dy);
        }
      }
      return path..close();
    }

    canvas.save();
    canvas.translate(size.width * .035, size.height * .035);
    canvas.drawPath(
      flower(size.shortestSide * .46, .6),
      Paint()..color = accent,
    );
    canvas.restore();
    canvas.drawPath(flower(size.shortestSide * .44, 0), Paint()..color = color);
  }

  @override
  bool shouldRepaint(_FlowerPainter oldDelegate) =>
      color != oldDelegate.color || accent != oldDelegate.accent;
}
