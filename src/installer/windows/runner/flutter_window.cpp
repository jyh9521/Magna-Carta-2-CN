#include "flutter_window.h"

#include <optional>
#include <filesystem>
#include <shobjidl.h>
#include <shellapi.h>
#include <dwmapi.h>
#include <flutter/standard_method_codec.h>
#include "utils.h"

#include "flutter/generated_plugin_registrant.h"

namespace {
std::wstring Wide(const std::string& text) {
  int size = MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.c_str(), -1, nullptr, 0);
  if (size == 0) return {};
  std::wstring result(size, L'\0');
  MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS, text.c_str(), -1, result.data(), size);
  result.resize(size - 1); return result;
}
}

FlutterWindow::FlutterWindow(const flutter::DartProject& project)
    : project_(project) {}

FlutterWindow::~FlutterWindow() {}

bool FlutterWindow::OnCreate() {
  if (!Win32Window::OnCreate()) {
    return false;
  }

  RECT frame = GetClientArea();

  // The size here must match the window dimensions to avoid unnecessary surface
  // creation / destruction in the startup path.
  flutter_controller_ = std::make_unique<flutter::FlutterViewController>(
      frame.right - frame.left, frame.bottom - frame.top, project_);
  // Ensure that basic setup of the controller was successful.
  if (!flutter_controller_->engine() || !flutter_controller_->view()) {
    return false;
  }
  RegisterPlugins(flutter_controller_->engine());
  SetChildContent(flutter_controller_->view()->GetNativeWindow());
  BOOL dark = TRUE;
  DwmSetWindowAttribute(GetHandle(), 20, &dark, sizeof(dark));
  channel_ = std::make_unique<flutter::MethodChannel<flutter::EncodableValue>>(
      flutter_controller_->engine()->messenger(), "mc2.desktop",
      &flutter::StandardMethodCodec::GetInstance());
  channel_->SetMethodCallHandler([this](const auto& call, auto result) {
    const auto& method = call.method_name();
    const auto* arg = call.arguments();
    if (method == "busy") {
      const bool* value = arg ? std::get_if<bool>(arg) : nullptr;
      busy_ = value && *value; result->Success(); return;
    }
    if (method == "close") {
      busy_ = false; result->Success(); PostMessage(GetHandle(), WM_CLOSE, 0, 0); return;
    }
    if (method == "blog") {
      auto status = reinterpret_cast<INT_PTR>(ShellExecuteW(GetHandle(), L"open", L"https://blog.blfy.cc/", nullptr, nullptr, SW_SHOWNORMAL));
      if (status <= 32) result->Error("open", "Windows did not open the link"); else result->Success();
      return;
    }
    const auto* text = arg ? std::get_if<std::string>(arg) : nullptr;
    if (!text) { result->Error("argument", "Expected a path or dialog title"); return; }
    auto value = Wide(*text);
    if (method == "openPath") {
      std::filesystem::path path(value);
      std::error_code ec;
      bool directory = std::filesystem::is_directory(path, ec);
      auto extension = path.extension().wstring();
      if (!directory && extension != L".txt" && extension != L".jsonl" && extension != L".json") {
        result->Error("path", "Only output directories and text reports may be opened"); return;
      }
      if (!std::filesystem::exists(path, ec)) { result->Error("path", "Path does not exist"); return; }
      INT_PTR status;
      if (directory) status = reinterpret_cast<INT_PTR>(ShellExecuteW(GetHandle(), L"open", value.c_str(), nullptr, nullptr, SW_SHOWNORMAL));
      else {
        wchar_t system[MAX_PATH]; GetSystemDirectoryW(system, MAX_PATH);
        auto editor = std::filesystem::path(system) / "notepad.exe";
        auto quoted = L"\"" + value + L"\"";
        status = reinterpret_cast<INT_PTR>(ShellExecuteW(GetHandle(), L"open", editor.c_str(), quoted.c_str(), nullptr, SW_SHOWNORMAL));
      }
      if (status <= 32) result->Error("open", "Windows did not open the output"); else result->Success();
      return;
    }
    if (method == "pickFile" || method == "pickDirectory") {
      IFileOpenDialog* dialog = nullptr;
      HRESULT status = CoCreateInstance(CLSID_FileOpenDialog, nullptr, CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&dialog));
      if (FAILED(status)) { result->Error("dialog", "Cannot create Windows file dialog"); return; }
      DWORD options = 0; dialog->GetOptions(&options);
      dialog->SetOptions(options | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST | FOS_FILEMUSTEXIST |
          (method == "pickDirectory" ? FOS_PICKFOLDERS : 0));
      dialog->SetTitle(value.c_str());
      if (method == "pickFile") {
        COMDLG_FILTERSPEC types[] = {{L"Xbox 360 ISO", L"*.iso"}, {L"All files", L"*.*"}};
        dialog->SetFileTypes(2, types);
      }
      status = dialog->Show(GetHandle());
      if (SUCCEEDED(status)) {
        IShellItem* item = nullptr;
        if (SUCCEEDED(dialog->GetResult(&item))) {
          PWSTR path = nullptr;
          if (SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH, &path))) {
            auto selected = Utf8FromUtf16(path); CoTaskMemFree(path); item->Release(); dialog->Release();
            result->Success(flutter::EncodableValue(selected)); return;
          }
          item->Release();
        }
      }
      dialog->Release();
      if (status == HRESULT_FROM_WIN32(ERROR_CANCELLED)) result->Success();
      else result->Error("dialog", "File selection failed");
      return;
    }
    result->NotImplemented();
  });

  flutter_controller_->engine()->SetNextFrameCallback([&]() {
    this->Show();
  });

  // Flutter can complete the first frame before the "show window" callback is
  // registered. The following call ensures a frame is pending to ensure the
  // window is shown. It is a no-op if the first frame hasn't completed yet.
  flutter_controller_->ForceRedraw();

  return true;
}

void FlutterWindow::OnDestroy() {
  channel_ = nullptr;
  if (flutter_controller_) {
    flutter_controller_ = nullptr;
  }

  Win32Window::OnDestroy();
}

LRESULT
FlutterWindow::MessageHandler(HWND hwnd, UINT const message,
                              WPARAM const wparam,
                              LPARAM const lparam) noexcept {
  if (message == WM_CLOSE && busy_ && channel_) {
    channel_->InvokeMethod("closeRequested", nullptr); return 0;
  }
  if (message == WM_GETMINMAXINFO) {
    auto* limits = reinterpret_cast<MINMAXINFO*>(lparam);
    const UINT dpi = GetDpiForWindow(hwnd);
    limits->ptMinTrackSize = {MulDiv(920, dpi, 96), MulDiv(720, dpi, 96)};
    return 0;
  }
  // Give Flutter, including plugins, an opportunity to handle window messages.
  if (flutter_controller_) {
    std::optional<LRESULT> result =
        flutter_controller_->HandleTopLevelWindowProc(hwnd, message, wparam,
                                                      lparam);
    if (result) {
      return *result;
    }
  }

  switch (message) {
    case WM_FONTCHANGE:
      flutter_controller_->engine()->ReloadSystemFonts();
      break;
  }

  return Win32Window::MessageHandler(hwnd, message, wparam, lparam);
}
