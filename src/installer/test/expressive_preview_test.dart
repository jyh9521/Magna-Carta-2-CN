import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mc2_installer/desktop.dart';
import 'package:mc2_installer/expressive_preview.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late List<MethodCall> calls;
  setUp(() {
    calls = [];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(Desktop.channel, (call) async {
          calls.add(call);
          return call.method == 'pickFile' ? r'D:\Originals\sample.iso' : null;
        });
  });
  Future<void> show(
    WidgetTester tester, {
    String variant = 'A',
    bool dark = false,
    Size size = const Size(1120, 820),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(
      ExpressivePreviewApp(
        initialVariant: variant,
        initialDark: dark,
        demoTick: const Duration(milliseconds: 20),
      ),
    );
    await tester.pumpAndSettle();
  }

  Future<void> settings(WidgetTester tester) async {
    await tester.tap(find.byKey(const Key('samples')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('next')));
    await tester.pumpAndSettle();
    expect(find.text('按你的方式，出发'), findsOneWidget);
  }

  for (final variant in ['A', 'B', 'C']) {
    for (final dark in [false, true]) {
      for (final size in [
        const Size(1120, 820),
        const Size(920, 720),
        const Size(760, 720),
      ]) {
        testWidgets(
          '$variant ${dark ? "dark" : "light"} ${size.width}: all four stages fit',
          (tester) async {
            await show(tester, variant: variant, dark: dark, size: size);
            expect(find.text('设计预览'), findsOneWidget);
            expect(find.text('准备好，开始新旅程'), findsOneWidget);
            expect(tester.takeException(), isNull);
            await settings(tester);
            expect(tester.takeException(), isNull);
            await tester.tap(find.byKey(const Key('format-XEX')));
            await tester.pumpAndSettle();
            await tester.tap(find.byKey(const Key('next')));
            await tester.pump(const Duration(milliseconds: 400));
            expect(find.byType(LinearProgressIndicator), findsOneWidget);
            expect(tester.takeException(), isNull);
            await tester.pump(const Duration(seconds: 2));
            await tester.pumpAndSettle();
            expect(find.text('演示流程已完成'), findsOneWidget);
            expect(find.textContaining('XEX  /  双盘 + DLC'), findsOneWidget);
            expect(tester.takeException(), isNull);
            expect(calls, isEmpty); // No channel traffic/backend during a demo.
          },
        );
      }
    }
  }
  testWidgets('required selection, optional DLC, actual path picker only', (
    tester,
  ) async {
    await show(tester);
    await tester.tap(find.byKey(const Key('next')));
    await tester.pumpAndSettle();
    expect(find.text('准备好，开始新旅程'), findsOneWidget);
    await tester.tap(find.byKey(const Key('dlc-toggle')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('dlc-pick')), findsNothing);
    await tester.tap(find.byKey(const Key('disc1')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('disc2')));
    await tester.pumpAndSettle();
    expect(calls.map((e) => e.method), ['pickFile', 'pickFile']);
    await tester.tap(find.byKey(const Key('next')));
    await tester.pumpAndSettle();
    expect(find.text('按你的方式，出发'), findsOneWidget);
  });
  testWidgets(
    'layout/theme retain paths format and stage; editable arrows do not cycle',
    (tester) async {
      await show(tester);
      await settings(tester);
      await tester.tap(find.byKey(const Key('format-XEX')));
      await tester.tap(find.byKey(const Key('theme')));
      await tester.tap(find.byKey(const Key('variant-next')));
      await tester.pumpAndSettle();
      expect(find.text('布局 B · 赤陶向导'), findsOneWidget);
      expect(find.text('按你的方式，出发'), findsOneWidget);
      expect(
        Theme.of(tester.element(find.byType(Scaffold))).brightness,
        Brightness.dark,
      );
      await tester.ensureVisible(find.byKey(const Key('output')));
      await tester.tap(find.byKey(const Key('output')));
      await tester.enterText(
        find.byKey(const Key('output')),
        r'D:\Preview\chosen',
      );
      await tester.sendKeyEvent(LogicalKeyboardKey.arrowRight);
      await tester.pumpAndSettle();
      expect(find.text('布局 B · 赤陶向导'), findsOneWidget);
      await tester.tap(find.byKey(const Key('variant-next')));
      await tester.pumpAndSettle();
      expect(find.text('布局 C · 青瓷工作台'), findsOneWidget);
      expect(find.text(r'D:\Preview\chosen'), findsOneWidget);
      await tester.tap(find.byKey(const Key('back')));
      await tester.pumpAndSettle();
      expect(find.text('MagnaCarta II (Korea) (Disc 1).iso'), findsOneWidget);
    },
  );
  testWidgets('error, retry and cancellation remain simulated', (tester) async {
    await show(tester);
    await settings(tester);
    await tester.tap(find.byKey(const Key('next')));
    await tester.pump(const Duration(milliseconds: 350));
    await tester.tap(find.byKey(const Key('error-demo')));
    await tester.pumpAndSettle();
    expect(find.text('演示：镜像摘要与支持版本不符'), findsOneWidget);
    await tester.tap(find.byKey(const Key('retry')));
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('先停一下，检查文件'), findsNothing);
    await tester.tap(find.byKey(const Key('back')));
    await tester.pumpAndSettle();
    expect(find.text('演示已取消 · 没有生成文件'), findsOneWidget);
    expect(calls, isEmpty);
    expect(tester.takeException(), isNull);
  });
  testWidgets('original logo remains unmodified and blog action works', (
    tester,
  ) async {
    await show(tester);
    final image = tester.widget<Image>(find.byType(Image));
    expect((image.image as AssetImage).assetName, 'assets/logo.png');
    expect(image.fit, BoxFit.contain);
    await tester.tap(find.text('伯翎飞云'));
    expect(calls.single.method, 'blog');
    expect(
      Theme.of(tester.element(find.byType(Scaffold))).useMaterial3,
      isTrue,
    );
  });
}
