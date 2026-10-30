import 'package:flutter/services.dart';

/// Windows system dialogs and ShellExecute; no runtime downloads or plugins.
class Desktop {
  static const channel = MethodChannel('mc2.desktop');
  static Future<String?> pick({bool directory = false, String title = ''}) =>
      channel.invokeMethod<String>(
        directory ? 'pickDirectory' : 'pickFile',
        title,
      );
  static Future<void> blog() => channel.invokeMethod('blog');
  static Future<void> open(String path) =>
      channel.invokeMethod('openPath', path);
  static Future<void> busy(bool value) => channel.invokeMethod('busy', value);
  static Future<void> close() => channel.invokeMethod('close');
}
