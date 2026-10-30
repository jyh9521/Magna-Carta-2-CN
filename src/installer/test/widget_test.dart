import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mc2_installer/backend.dart';
import 'package:mc2_installer/desktop.dart';
import 'package:mc2_installer/main.dart';

class TestBackend extends Backend {
  TestBackend() {
    loading = false;
    info = {
      'version': 'fixture',
      'required_zar': 22000000000,
      'required_xex': 19000000000,
    };
  }
  Map<String, dynamic>? lastRequest;
  @override
  Future<bool> run(Map<String, dynamic> request) async {
    lastRequest = request;
    success = true;
    return true;
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late List<MethodCall> calls;
  setUp(() {
    calls = [];
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(Desktop.channel, (call) async {
          calls.add(call);
          return null;
        });
  });
  Future<TestBackend> show(
    WidgetTester tester, {
    Size size = const Size(1080, 870),
  }) async {
    tester.view.physicalSize = size;
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final backend = TestBackend();
    await tester.pumpWidget(InstallerApp(backend: backend));
    await tester.pumpAndSettle();
    return backend;
  }

  testWidgets('latest logo is centered, intact, and footer blog is clickable', (
    tester,
  ) async {
    await show(tester);
    final image = find.byType(Image);
    expect(image, findsOneWidget);
    final widget = tester.widget<Image>(image);
    expect(widget.fit, BoxFit.contain);
    expect((widget.image as AssetImage).assetName, 'assets/logo.png');
    expect(tester.getCenter(image).dx, closeTo(540, 1));
    expect(tester.getCenter(find.text('伯翎飞云')).dx, greaterThan(950));
    expect(tester.getCenter(find.text('伯翎飞云')).dy, greaterThan(820));
    await tester.tap(find.text('伯翎飞云'));
    await tester.pump();
    expect(calls.last.method, 'blog');
    expect(
      Theme.of(tester.element(find.byType(Scaffold))).useMaterial3,
      isTrue,
    );
    expect(tester.takeException(), isNull);
  });
  testWidgets('required input validation and DLC selection', (tester) async {
    await show(tester);
    await tester.tap(find.text('检查文件并继续'));
    await tester.pumpAndSettle();
    expect(find.text('请选择Disc 1 ISO'), findsOneWidget);
    await tester.tap(find.byType(SwitchListTile));
    await tester.pumpAndSettle();
    expect(find.widgetWithText(TextFormField, '原版 DLC 文件夹'), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets('logo has no backdrop and header controls stay clear', (
    tester,
  ) async {
    await show(tester);
    final logo = tester.getRect(find.byType(Image));
    expect(
      tester.getTopLeft(find.text('MAGNACARTA II\nLOCALIZATION')).dx,
      lessThan(64),
    );
    expect(
      tester.getTopLeft(find.byTooltip('输入与兼容性说明')).dx,
      greaterThan(logo.right + 100),
    );
    final gradients = tester
        .widgetList<DecoratedBox>(find.byType(DecoratedBox))
        .where(
          (w) =>
              w.decoration is BoxDecoration &&
              (w.decoration as BoxDecoration).gradient != null,
        );
    expect(gradients, isEmpty);
  });
  testWidgets('step connectors are separated from every button background', (
    tester,
  ) async {
    await show(tester, size: const Size(920, 720));
    const labels = ['原版文件', '输出设置', '安装过程', '完成结果'];
    final lines = find.byType(Divider);
    expect(lines, findsNWidgets(3));
    for (var i = 0; i < 3; i++) {
      final left = find
          .ancestor(
            of: find.text(labels[i]),
            matching: find.byType(AnimatedContainer),
          )
          .first;
      final right = find
          .ancestor(
            of: find.text(labels[i + 1]),
            matching: find.byType(AnimatedContainer),
          )
          .first;
      expect(
        tester.getRect(lines.at(i)).left - tester.getRect(left).right,
        greaterThanOrEqualTo(8),
      );
      expect(
        tester.getRect(right).left - tester.getRect(lines.at(i)).right,
        greaterThanOrEqualTo(8),
      );
    }
    expect(tester.takeException(), isNull);
  });
  testWidgets('format selection and second page use real backend request', (
    tester,
  ) async {
    final backend = await show(tester);
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'C:\\original1.iso');
    await tester.enterText(fields.at(1), 'C:\\original2.iso');
    await tester.enterText(fields.at(2), 'C:\\DLC');
    await tester.tap(find.text('检查文件并继续'));
    await tester.pumpAndSettle();
    expect(backend.lastRequest?['operation'], 'inspect');
    expect(find.text('选择你的游玩方式'), findsOneWidget);
    await tester.tap(find.text('XEX · 实机 / Xenia'));
    await tester.pumpAndSettle();
    expect(find.textContaining('输出 Disc1 / Disc2'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
  testWidgets('light mode and minimum window have no overflow', (tester) async {
    await show(tester, size: const Size(920, 720));
    await tester.tap(find.byTooltip('切换浅色主题'));
    await tester.pumpAndSettle();
    expect(
      Theme.of(tester.element(find.byType(Scaffold))).brightness,
      Brightness.light,
    );
    expect(find.text('伯翎飞云'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
