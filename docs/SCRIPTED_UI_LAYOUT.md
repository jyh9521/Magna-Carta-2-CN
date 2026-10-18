# Scripted UI layout paths — 2026-10-19

## Verified offline scope

The opt-in `inspect_function_metadata.py --include-scripted` now decodes all5
previously unparsed scripted UIComp_DrawString methods. With the original Core
reference, the full immediate-Class inventory contains18 native parameter stubs
and5 scripted bodies,23/23 parsed,0 unparsed. Default native-only behavior still
reports18/5 and exit1; the opt-in run returns exit0. Neither mode executes code.

Original source identities:

- Engine.xxx: `f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a`.
- Core.xxx: `1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815`.
- Both use big-endian446/licensee25. Source packages/configuration remain unchanged.

The5 bodies consume736 serialized bytes and242 decoded tokens completely:
SetWrapMode76; SetClipAlignment76; IsAutoSizeEnabled33;
EnableAutoSizing118; SetAutoSizePadding433. These are logical serialization
offsets and byte counts, not native addresses or runtime object layouts.

## Field/control paths, not display acceptance

**Verified source syntax and references:**

| Method/export | Direct source writes / reads | Control path |
| --- | --- | --- |
| SetWrapMode15584 | reads/writes bReapplyFormatting15531; writes WrapMode15538 from NewClipMode15583 | conditional jump at45, target73; update call at54 |
| SetClipAlignment15586 | reads/writes bReapplyFormatting15531; writes ClipAlignment15537 from NewClipAlignment15585 | conditional jump45 ->73; update call54 |
| IsAutoSizeEnabled15589 | returns AutoSizeParameters15536[int(Orientation15588)].bAutoSizeEnabled5279 | explicit Return at0; compiler ReturnNothing tail at26 has no syntactic incoming edge |
| EnableAutoSizing15593 | optional bShouldEnable15591 defaults true; local bNeedsReformatting15590; writes indexed bAutoSizeEnabled and bReapplyFormatting | conditional jump87 ->115; update call96 |
| SetAutoSizePadding15600 | local bNeedsReformatting15594; writes indexed Padding.Value[0/1] and Padding.ScaleType[0/1], then bReapplyFormatting | conditional jump402 ->430; update call411 |

The four update sites encode `Context(self.Outer,
UIScreenObject.RequestSceneUpdate(false, true, <omitted>, <omitted>))`.
Outer is the actual imported Core.Object.Outer reference(-86), not a guessed
component owner field. The callee is Engine Function5791. Its ordered parameters
are bDockingStackChanged(false), bPositionsChanged(true), bNavLinksOutdated
(omitted/optional) and bWidgetStylesChanged(omitted/optional). The callee body is
not decoded/executed by this analysis; the occurrence of a request does not
prove that a scene updates or how native rendering reacts.

Padding.Value5265 and ScaleType5264 belong to UIScreenValue_Position;
AutoSizePadding5278 inherits that struct. The reader accepts this through the
verified struct super chain, not a same-name field search. AutoSizeData5282
contains Padding5280 and bAutoSizeEnabled5279. Dynamic Orientation indices retain
runtime_index_bounds_verified=false: enum/type identity is not a runtime range
check. No glyph width, wrapping/clipping pixels or effective Font is measured.

**High-confidence source-level interpretation:** the declared operators express
preserving an existing formatting-dirty flag while adding change comparisons.
The padding method compares both near/far values and scale types before the
four writes. These methods condition the update request on bReapplyFormatting.
They contain no direct DrawFont write in the decoded bodies. Indirect native
effects and whether any method is actually called remain unverified.

## Operator declarations and bounded grammar

Native operators are not guessed from numeric constants or a generic online
table. The reader inventories all239 immediate Core.Object Function metadata
headers, binds a unique nonzero NativeToken within that scope, then verifies
the selected native declaration/parameter stub:

| Token | Core export | Stored name/alias |
| --- | --- | --- |
|132|218|Object.OrOr_BoolBool / `||`|
|155|308|Object.NotEqual_IntInt / `!=`|
|181|419|Object.NotEqual_FloatFloat / `!=`|
|243|206|Object.NotEqual_BoolBool / `!=`|

Operator aliases legitimately differ from export leaves and are admitted only
when the serialized operator flag is set; non-operator FriendlyName mismatches
still fail. This establishes declaration identity, **not executable native
registration or implementations**. Missing Core, missing/duplicate token
declarations or a token that is not an operator fails the scripted record.

Supported tokens are deliberately restricted: local/instance variables,
Return/ReturnNothing/Nothing, Let/LetBool, JumpIfNot, Skip, Context, static
ArrayElement, FinalFunction, IntZero/IntOne/True/False, BoolVariable,
StructMember, ByteToInt(0x38/0x3a), DefaultParmValue/EndParmValue,
EmptyParmValue/EndFunctionParms, EndOfScript and direct native-operator tokens
0x70..0xff. Unknown and extended-native opcodes are not silently skipped.

The reader checks local ownership, instance-Class ancestry, struct-member
ownership including inherited fields, declared struct context, scalar/static
array dimensions, enum identities, supported argument/return types, out lvalues,
optional omissions and Skip flags. It validates complete forward JumpIfNot
targets against top-level statement boundaries, short-circuit Skip spans and
optional-default spans/terminators. Defaults must precede the body; a wrapper
must end with Return and one final EndOfScript. Nesting is bounded64, tokens8192,
arguments256 and type ancestry256. Existing Function size bound10242 remains.

For this subset, short-circuit Skip includes the enclosing EndFunctionParms byte;
default-value size includes EndParmValue. The Context raw skip word is5 at the
four actual call sites; its VM meaning is **not inferred or marked verified**.
The parser retains its raw word and property-type byte0 while decoding the
following call syntax. It is not a general bytecode verifier or UE3 evaluator.

Reports include typed ASTs, logical token positions, source-like statements
with explicit labels/Skip/omitted/ReturnNothing markers, and syntactic control
edges/reachability without evaluating conditions or invoking native calls.
Source-like output is not original source recovery or a runtime trace.

## Reproduce and validate

```powershell
python tools/inspect_function_metadata.py build/poc-game/disc1/MC2Game/CookedXenon/Engine.xxx --sha256 f71131de2a39176f48d5bf7ef6ed803513d5b38303f21915029c245442b8fe9a --class UIComp_DrawString --include-scripted --reference-package Core build/poc-game/disc1/MC2Game/CookedXenon/Core.xxx 1f79abbc4c0992e4c2eef33e755af6a9993dc980cdf053677e9b138f0cecb815 --lzx-library build/lzx/native-verified/ue3_lzx.dll --output build/NEW-scripted-ui.json
```

Only new reports are written. All source hashes/profiles, including references,
are checked before optional decoder loading; reports are reopened and package
snapshots are rechecked. Source files are not patched. Exit0 means all selected
records parsed,1 means explicit partial records,2 means input/output/profile
failure. Every report retains game_rendering_verified=false and
native_implementation_verified=false.

Twenty-three new self-authored fixture tests cover complete synthetic package CLI
input, exact native-operator binding, owned/inherited fields, arrays/casts,
argument/default/out/Skip constraints, statement targets, syntactic reachability,
all truncations of a parameterized scripted body, depth limits, unknown tokens,
return markers, opt-in mode, source/reference hash guards before decoder load
and unverified Context skip preservation. They use no game files, fonts or DLL.
Full regression:415 baseline ->438 modified ->415 independent source rollback;
native-decoder-enabled438. Commands/raw results remain locally under ignored
build/scripted-ui-verification/.

## Provenance and remaining work

Independent format research uses Eliot van Uytfanghe's MIT Unreal-Library commit
`8236c39b79e30887a487ecf9b018204e430a5ebc`, token readers and ExprToken/CastToken
definitions. Exact source URLs/hashes are in references/scripted-ui-research.lock.json;
earlier locks retain native metadata, FieldTokens and version/token maps.
No upstream runtime/source is integrated. General REA opening of this same .xxx
previously returned unsupported format; no native session is claimed here.

Remaining offline work follows executable native registration/implementation
for SetFont, DisableCustomFont and the two style getters, plus constructor and
renderer measurement paths. This script analysis does not settle active Font,
Chinese glyph placement or native side effects. The user alone performs game
testing; no launch, input, deployment, configuration change or bulk story
translation is part of this milestone.
