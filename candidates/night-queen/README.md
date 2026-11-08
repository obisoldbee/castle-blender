# Night Queen / 夜之女王：未通过验收的独立候选

仅归档供审查，不替换城堡主场景或动画中的滴水兽。当前人物造型被用户否定，尤其脸部还原度、表情、冠与鸟爪；不是最终作品。

## 文件
- `models/Night_Queen_Serene_Study.blend`：当前候选，Blender 4.3.2。
- `models/Night_Queen_Articulated_Toes.blend`：上一阶段脚趾版，供比较。
- `previews/`：实际 Blender 渲染，不是原物照片。toes_front 是脚趾阶段，serene_* 为当前候选。
- `references/`：原物照片与许可，见 SOURCES.md。
- `historical-patches/`：历史修订脚本，依赖未包含的 build.py/更早模型，不可独立重建。不得以此宣称完整可复现；不会自动执行。

安全打开：`blender --disable-autoexec candidates/night-queen/models/Night_Queen_Serene_Study.blend`。

## 审查重点与已知问题
1. 对照原物的脸宽、下颌、鼻唇、眼睑与祥和表情，避免现代人体底模只局部推拉的僵硬效果。用户“更像亚洲面孔”是审美方向，不是古代族群结论。
2. 冠应覆盖头顶、有连续多层成对角饰，不是中央棍连接的秃顶笼架。当前删除中央连接杆仍未达到原物轮廓。
3. 鸟爪应有粗长脚趾、显著大关节和横向褶皱；核查脚踝到爪根过渡、趾尖落点、承重与爪尖，不把重复波纹当真实结构。
4. 手持环杆的握持关系、肘部折叠、肩翼连接、羽片密度与发束仍需修改。
5. 场景有两处遗留眼球对象，位置约 x=2.2、z=5.27，需检查清理。人物高约2.9409m、含底座3.2557m；原浮雕整块49.5×37×4.8cm，绝非等比复原。
6. 狮子、猫头鹰未建；侧背面是现代补全，不冒称考古复原。

审查应分别给证据、优先级、具体几何改法、验收相机/指标；没有实际读取 blend 时须明说，不能用图片推断拓扑检查已完成。

## Review follow-through
See [REVIEW_ACTIONS.md](REVIEW_ACTIONS.md). A separate technical-cleanup successor is in `remediation/`; it is **not** a visually accepted revision.

## Actual reconstruction study
`reconstruction-v01/` contains rebuilt geometry, four actual verification renders, source modules and scoped measurements. Self-review **not passed**: see its README for remaining failures. It is not a final replacement.
