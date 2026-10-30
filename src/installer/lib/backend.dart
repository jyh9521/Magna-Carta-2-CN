import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

class Backend extends ChangeNotifier {
  Backend({String? executable})
    : executable =
          executable ??
          '${File(Platform.resolvedExecutable).parent.path}\\backend\\mc2-patch.exe';
  final String executable;
  Map<String, dynamic>? info;
  Process? _process;
  bool loading = true, busy = false, cancelling = false, success = false;
  double progress = 0;
  String stage = '', message = '', error = '', output = '', logPath = '';
  final List<Map<String, dynamic>> events = [];

  Future<void> initialize() async {
    try {
      final result = await Process.run(
        executable,
        ['--info'],
        stdoutEncoding: utf8,
        stderrEncoding: utf8,
      );
      if (result.exitCode != 0) {
        throw Exception('${result.stdout}\n${result.stderr}');
      }
      info = jsonDecode(
        (result.stdout as String).trim().split('\n').last,
      ) as Map<String, dynamic>;
    } catch (e) {
      error = '安装组件加载失败。请完整解压安装包后运行。\n$e';
    }
    loading = false;
    notifyListeners();
  }

  void _event(Map<String, dynamic> event) {
    events.add(event);
    if (events.length > 2000) events.removeAt(0);
    stage = event['stage'] as String? ?? stage;
    message = event['message'] as String? ?? message;
    progress = (event['progress'] as num?)?.toDouble() ?? progress;
    logPath = event['log_path'] as String? ?? logPath;
    output = event['output'] as String? ?? output;
    if (stage == 'failed') error = message;
    if (stage == 'complete' || stage == 'inspected' || stage == 'recovered') {
      success = true;
    }
    notifyListeners();
  }

  Future<bool> run(Map<String, dynamic> request) async {
    if (busy || loading || info == null) return false;
    busy = true;
    cancelling = false;
    success = false;
    progress = 0;
    error = '';
    logPath = '';
    message = '准备检查';
    stage = 'prepare';
    events.clear();
    notifyListeners();
    Directory? temp;
    try {
      temp = await Directory.systemTemp.createTemp('mc2-installer-request-');
      final file = File('${temp.path}/request.json');
      await file.writeAsString(
        jsonEncode(request),
        encoding: utf8,
        flush: true,
      );
      final process = await Process.start(executable, ['--request', file.path]);
      _process = process;
      if (cancelling) process.stdin.writeln('cancel');
      final stdoutDone = process.stdout
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .forEach((line) {
            try {
              _event(jsonDecode(line) as Map<String, dynamic>);
            } catch (_) {
              _event({'level': 'debug', 'message': line});
            }
          });
      final stderrDone = process.stderr
          .transform(utf8.decoder)
          .transform(const LineSplitter())
          .forEach((line) => _event({'level': 'error', 'message': line}));
      final exit = await process.exitCode;
      await Future.wait([stdoutDone, stderrDone]);
      if (exit == 130) {
        stage = 'cancelled';
        success = false;
      } else if (exit != 0 || !success) {
        success = false;
        if (error.isEmpty) error = '处理未完整结束（退出码 $exit）。请查看日志后重试。';
      }
    } catch (e) {
      success = false;
      error = '$e';
      stage = 'failed';
    } finally {
      _process = null;
      // Exclusively owned request directory; never holds installation files.
      try {
        if (temp != null) {
          final file = File('${temp.path}/request.json');
          if (await file.exists()) await file.delete();
          await temp.delete();
        }
      } on FileSystemException catch (e) {
        events.add({'level': 'warning', 'message': '请求文件清理未完成：$e'});
      }
      busy = false;
      cancelling = false;
      notifyListeners();
    }
    return success;
  }

  void cancel() {
    if (!busy || cancelling) return;
    cancelling = true;
    _process?.stdin.writeln('cancel');
    message = '正在取消并清理本次临时文件…';
    notifyListeners();
  }
}
