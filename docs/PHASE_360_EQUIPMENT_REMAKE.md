# 阶段360：装备立绘重新制作及实测修复队列

## 用户纠正与范围

截图中的 `Argo style Hammer` 是角色／武器流派的烘焙字图，不是独立职业字段。
已定位14张英文立绘、双盘54个物理Texture2D别名；乡村朱特原有中文立绘保持。
首版中文预览被用户明确否决：旧英文光晕及描边残留成横条，背景糊化；随后指出中文字向左倾，与原版右倾相反。
被否决的v29及局部纹理克隆v30仅保留为忽略的研究证据，不作为发布候选。

## Verified：斜切方向

`source-style-v1` 使用Pillow的逆向仿射采样。`italic`为正时，字形顶部相对底部向右移动；负值向左。
本轮错误在locale计划的负参数，不在通用变换函数；不更改其他图片的历史渲染语义。
14张图片的角色名、较小的“流派”和武器名共42段全部采用正值`+0.18`。
回归不仅检查参数，还用自绘矩形字形比较真实光栅顶部／底部行的中心，分别证明正、负和零值的方向。

## Verified：残留不能只检查RGB

原版白字、黑色边缘及红色光晕已经与人物背景烘焙在同一图中；部分英文还写入人物轮廓外的alpha。
仅删除亮字芯会把红光平均成宽条；只修RGB而保留全部alpha，则在棋盘底上仍可看到黑色旧字轮廓。

新候选从原图重做，使用文字清除后的图像生成结果作为局部背景参考，再以固定迭代和源边界颜色重建稀疏修复片段。
完整生成立绘不替换原人物，也不进入公开源资产；生产计划只依赖小型patch／mask PNG、明确原始资源散列与固定字体。
被原字遮挡的衣料／盔甲属于**重建**，不宣称找回原画。

- 重建只在明确旧字、描边、阴影及光晕支持域内进行，域外源RGBA在编码前逐字节保持。
- 必要的alpha修复仅在该域内沿用原生alpha边界推导，避免直接采用生成图轮廓而切掉原有黑色笔刷。
- 中文重新绘制后编码为实际Xbox BC3，再回读成品；检查常规底色与棋盘透明底。
- 双盘物理别名使用有界原生块转移，不以整个供体包覆盖当前资源，保留既有字体与界面修订。
- 通用`parts`层支持同一授权区域内不同字号／色效的短文字段，父文本必须等于子文本按序连接；拒绝嵌套、异源字体和越界字段。

## 另外三类实测报告

详见[游戏实测修复列表](GAMEPLAY_FIX_LIST.md)：剧情过场后的大章节名、所有Boss过场后特写名称、锁链封印场景的特殊镜头大字。
这些报告的资源定位和游戏内修复状态独立于装备立绘；不以地图目的地视频的研究或既有场景入口汉化替代验收。

现已直接在原盘`csm00-35.bik`第210帧核实“가디언 아몬”特写标题烘焙于电影像素。
既有15张Boss UI模板及67个物理别名已中文、安装器985项资源一致，仍然不覆盖这条独立的视频显示路线。
所以后续Boss验证须从实际过场资源出发，不得再以UI模板清单通过代替过场后特写验收。

调查中另外发现11段带韩文目的地的地图转场视频，但用户没有确认它们就是“大章节名称”。
新增音轨保留／源锁定工具及合成夹具验证属于研究进展；未将这些视频部署为已完成的章节修复。

## 可复用的局部清字提示词

内置`image_gen.imagegen`用于参考底图；保存的稀疏PNG才是可重现的生产输入，随机重新生成不会得到相同字节。

```text
Edit the supplied original portrait into a text-free clean plate. Remove only
the original lettering and its complete white ink, black outline/shadow and
red/orange halo. Continue the underlying original fabric, armor and silhouette
without blur bands, flat rectangles or letter-shaped alpha residue. Preserve
the exact pose, face, costume, framing, colors, lighting and transparency.
Do not add text or redesign the character. The generated full portrait is only
a repair guide: production must retain original pixels outside the explicitly
owned old-lettering support.
```

## 验证边界

源版本、构建命令、实际三态输出、双盘身份、独立恢复及发布检查记录在本轮`VERIFICATION.txt`。
离线字节／方向／透明度检查不替代用户美术确认或实际游戏渲染验收。
