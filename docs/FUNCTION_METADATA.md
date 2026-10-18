# UI function declarations and native-stub boundary — 2026-10-19

## Verified offline

The source remains Engine.xxx SHA-256
`f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a`,
big-endian UE3 package446/licensee25. No game, emulator or function is executed.

All23 immediate Core.Function exports of Engine Class15601
UIComp_DrawString were inventoried by export outer, not by leaf-name search.
Eighteen have native declarations and exact parameter-only scripts. Five are
explicitly unparsed by the default **native-only** mode; they are not empty methods
or failures of the original game. This resolves the package/native boundary,
not native registration, implementation or effective font selection.

| Question / scoped export | Stored declaration | Stored script |
| --- | --- | --- |
| SetFont15555 | NewFont15554: ObjectProperty, target Engine.Font4920, Parm | NativeParm(NewFont), Nothing, EndOfScript |
| DisableCustomFont15563 | no parameter or return declaration | Nothing, EndOfScript |
| GetAppliedStringStyle15568 | DesiredMenuState15567: optional Engine.UIState20135; ReturnValue15566: Engine.UIStyle_Combo20223 | NativeParm(DesiredMenuState), Nothing, EndOfScript |
| GetFinalStringStyle15571 | FinalStyleData15570: out StructProperty, UIRoot.UICombinedStyleData5390; ReturnValue15569: BoolProperty | NativeParm(FinalStyleData), Nothing, EndOfScript |
| GetStyleResolverTag15573 | ReturnValue15572: NameProperty | Nothing, EndOfScript |
| SetStyleResolverTag15576 | NewResolverTag15575: NameProperty; ReturnValue15574: BoolProperty | NativeParm(NewResolverTag), Nothing, EndOfScript |
| NotifyResolveStyle15582 | ActiveSkin15581, bClearExistingValue15580, CurrentMenuState15579 (optional), StylePropertyName15578 (optional); ReturnValue15577: BoolProperty | four NativeParm tokens in declaration-chain order, Nothing, EndOfScript |

The full supported set is SetValue, GetValue, RefreshValue, SetColor, SetOpacity,
SetFont, SetAttributes, SetAlignment, DisableCustomColor, DisableCustomOpacity,
DisableCustomFont, DisableCustomAttributes, DisableCustomAlignment,
GetAppliedStringStyle, GetFinalStringStyle, GetStyleResolverTag,
SetStyleResolverTag and NotifyResolveStyle.

All18 store NativeToken=0 and operator precedence0. Their raw FunctionFlags are
0x00020401 except GetFinalStringStyle0x00420401. Native is bit0x400; the raw flags
and token are metadata, **not an observed C++ address or dispatch resolution**.
Return declarations are not included among NativeParm script tokens.

The five unsupported non-native methods are SetWrapMode15584,
SetClipAlignment15586, IsAutoSizeEnabled15589, EnableAutoSizing15593 and
SetAutoSizePadding15600. The class report records each with its reason and
returns exit1. No claim is made that their script behavior has been decoded.

## Exact retained metadata profile

The UObject prefix is NetIndex i32 followed by an empty None FName tag list.
At relative12 the UField/UStruct words are:

| Relative offset | Serialized field |
| --- | --- |
|12|Super reference, must equal export-table super|
|16|NextField reference|
|20|ScriptText reference0|
|24|Children reference|
|28|CppText reference0|
|32|Line, nonnegative (SetFont282)|
|36|TextPos, nonnegative (SetFont7250)|
|40|Script size (SetFont7)|
|44|Exact supported parameter stub|

Unlike the data-only ScriptStruct profile, these functions retain **nonzero**
Line/TextPos. After the stub the reader consumes native token u16BE, precedence
u8, FunctionFlags u32BE and the retained FriendlyName FName. For SetFont the
script starts logical3203183, the metadata tail starts3203190; the66-byte export
is fully consumed. FriendlyName must match the export leaf and have number0.
Do not strip it merely because the package is Xenon/cooked.

The supported stub is exactly `(0x29 + property-reference-i32BE)* 0x0b 0x53`:
NativeParm, Nothing and EndOfScript. Script sizes in the18 methods are2/7/12/22.
For this subset the declared size matches the serialized stub size. The reader
does **not** generalize this equality to arbitrary v446 bytecode; it accepts
only the complete recognized shape and verified property chain. Unknown tokens
and extra bytes are rejected, never treated as an opaque successful body.

Shared property_chain validates bounded, positive, acyclic local links,
matching owners, unique names and completeness against all immediate property
exports. Parameters retain native declaration types/targets/raw flags.
Parm=0x80, OptionalParm=0x10, OutParm=0x100 and ReturnParm=0x400 are decoded;
at most one return is accepted. Non-parameter locals are unsupported here.
The ordered NativeParm references must exactly equal the declaration chain
excluding returns, not sorted export indices or arbitrary in-range objects.

The new parser also rejects stack/CDO prefixes, nonempty metadata UObject tags,
wrong Core.Function classes, mismatched supers, non-Class owners, nonzero
ScriptText/CppText, negative editor positions, networked flags, non-native
flags, invalid script sizes, malformed FNames and truncated/trailing data.
Bounds are2048 declarations and10242 supported script bytes. Native tokens and
operator bytes are retained, not used to execute or resolve anything.

## Reproduce

```powershell
python tools/inspect_function_metadata.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --object UIComp_DrawString.SetFont --object UIComp_DrawString.DisableCustomFont --object UIComp_DrawString.GetAppliedStringStyle --object UIComp_DrawString.GetFinalStringStyle --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-function-metadata.json
python tools/inspect_function_metadata.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --class UIComp_DrawString --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-drawstring-functions.json
```

The first selection returns exit0; the class inventory returns exit1 with
18 supported and5 explicit unparsed records. Exit2 indicates an input/output/
profile failure. Object selection and immediate-class inventory are mutually
exclusive. Reports must be new and distinct from inputs; output is reopened
and original package bytes are checked again. All reports have
native_implementation_verified=false and game_rendering_verified=false.

Eighteen synthetic regression tests use self-authored metadata and an actual
synthetic package CLI input, including every function-payload truncation,
all single-byte mutations of a parameter stub, scoped declarations/ordered
references, parameter flags/returns, editor headers, tail/FName validation,
unsupported profiles and CLI failures. They need no game assets or DLL.
Full regression:397 baseline ->415 modified ->397 independent source rollback;
native-decoder-enabled415. Full local commands/results live under the ignored
build/function-metadata-verification/ directory, not in game data.

## Provenance and next evidence

Format research uses Eliot van Uytfanghe's MIT Unreal-Library commit
`8236c39b79e30887a487ecf9b018204e430a5ebc`:
[UFunction](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Classes/UFunction.cs),
[FieldTokens](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Tokens/FieldTokens.cs),
[OtherTokens](https://github.com/EliotVU/Unreal-Library/blob/8236c39b79e30887a487ecf9b018204e430a5ebc/src/Core/Tokens/OtherTokens.cs).
Their exact source hashes are locked in references/function-metadata-research.lock.json.
Existing struct-default and UI-style locks retain UField/UStruct/UProperty,
DefaultEngineBranch's token/flag maps and version constants. The implementation
is independent Python; no upstream runtime/source is integrated.

The previous REA attempt on this same hash-locked .xxx returned unsupported
format, without a native session. That boundary remains; this is format-aware
package evidence, not native-code decompilation or runtime evidence.

**Still unverified:** native constructor defaults; calls that enable/disable
overrides; actual selected Font at drawing; renderer metrics and Chinese pixels.
The native-only milestone left five scripted wrappers as the next lead; their
opt-in follow-up is below. Executable native registration/implementation remains open. A name alone proves neither call
order nor implementation; serialized null/default flags do not prove runtime
absence of an override. Game testing remains exclusively with the user.


## Opt-in scripted follow-up

The later --include-scripted mode with a hash-locked Core reference fully decodes the5 scripted siblings (23/23 class exports total). Default native-only results above remain reproducible. See SCRIPTED_UI_LAYOUT.md for typed AST/control paths, Core operator aliases, source-hash preflight and explicit Context/native/runtime limits.
