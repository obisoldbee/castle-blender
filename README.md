# 城堡 Blender 项目

程序化城堡主场景、24 小时昼夜动画和滴水兽特写。项目不含小天使。

## 当前状态

已按用户认可的试作将塔屋顶高度缩至 65%，并按用户最新要求移除全部 20 组屋面窗及其小球，保留主尖顶顶饰。两份工程已重建并回归；夜景、黄昏灯光及相机保持不变。详见 [屋顶比例整改](docs/roof-proportions.md)。

已修复并重建两份 `.blend`：同步滴水兽及托座、恢复默认相机与采样、修正昼夜循环接缝。结构、循环几何与低清关键帧已检查；完整 720 帧成片未渲染。高网格海面在当前约 9.7 GiB 共享内存环境渲染被系统结束，诊断图使用临时低网格且有噪点，不代表最终画质。详见 [整改记录](docs/audit-fixes.md)。

`castle/anim/review3/contact_sheet.jpg` 和仓库内既有特写、静帧是历史产物，不是本轮修复的验收图，保留供比较。原资产保留在 Git 历史，不复制大文件作为备份。

## 入口

- `castle/castle.py`：生成主场景；默认只构建，显式选择后才渲染。
- `castle/castle.blend`：主场景交付入口，是否已更新以整改记录的验收状态为准。
- `castle/anim.py`：从干净、已保存的主场景生成周期动画。
- `castle/anim/castle_24h.blend`：动画交付入口，默认渲染范围 1–720 帧、24 fps。
- `castle/gargoyle_closeups/shots.py`：准备或渲染滴水兽特写。
- `castle/gargoyle_closeups/fix/gargfix.py`：识别旧场景的有界迁移补丁，不是任意模型修复工具。

## 安全打开

当前开发检查使用 Blender 4.3.2；Blender 4.2 尚未验证。不要把 4.2 视为已确认兼容版本。

```sh
blender --disable-autoexec castle/castle.blend
```

脚本依赖 Blender 自带的 `bpy`、`bmesh`、`mathutils` 和 Python 标准库。运行脚本会修改内存场景并可能保存文件；`castle.py` 会清空当前场景。请使用独立 Blender 进程，不在未保存的工作中运行。参数和输出覆盖检查在场景修改前执行，但不代替备份。

## 构建和渲染

以下命令从仓库根目录执行；每次选择新的输出目录，示例路径不应与已有交付物重叠。

```sh
# 默认仅构建；主场景默认 64 samples，保存为 builds/main-v1/castle.blend。
blender -b --python castle/castle.py -- --output-dir builds/main-v1

# 显式生成并渲染一张静帧；64 为样本数，后面可选相机名。
blender -b --python castle/castle.py -- 64 Cam_Wide --mode render --output-dir builds/still-v1

# 每次从干净主场景开始；动画默认 32 samples、1280×720，仅构建。
blender -b builds/main-v1/castle.blend --python castle/anim.py -- build --output-dir builds/animation --build-id cycle-v1

# 显式渲染完整动画；final 默认 32 samples，可通过 --samples 提高。
blender -b builds/main-v1/castle.blend --python castle/anim.py -- final --render --samples 32 --output-dir builds/animation --build-id cycle-render-v1

# 显式渲染低分辨率关键帧（keys 模式为 640×360、12 samples）。
blender -b builds/main-v1/castle.blend --python castle/anim.py -- keys --render --output-dir builds/animation --build-id keys-v1
```

主脚本支持 `--night`、四个相机名 `Cam_Wide` / `Cam_Low` / `Cam_Moon` / `Cam_Gate`。主场景及特写输出文件已存在时拒绝覆盖；只有明确传入 `--force` 才允许覆盖。保存的主场景使用相对渲染路径 `//output/…`；显式脚本静帧渲染写入所选输出目录。

动画脚本拒绝重复加工已经动画化的场景。动画输出位于 `--output-dir` 下独立构建子目录：指定 `--build-id`，或使用输入、脚本、参数等生成的指纹。已存在的子目录一律拒绝复用，包括半成品目录，避免混入旧帧。`build.json` 记录构建身份，帧输出使用相对路径 `//frames/`。

无 OpenImageDenoise 支持的 Blender 构建，可显式加入 `--no-denoise` 做诊断；这不保证低采样画面的质量。`preview` 模式是 640×360、8 samples、每 4 帧；没有 `--render` 仍然不渲染。

特写默认只准备相机，不保存场景、不渲染。需要图片时：

```sh
blender -b builds/animation/cycle-v1/castle_24h.blend --python castle/gargoyle_closeups/shots.py -- 64 all 100 --mode render --output-dir builds/closeups-v1
```

特写可把 `all` 换成 `g1_threequarter_day`、`g2_profile_day`、`g3_from_below` 或 `g4_dusk`；最后一个位置参数为分辨率百分比。旧场景布局不匹配时补丁会拒绝执行，不盲目平移或重复添加托座。

## 边界与来源

模型仍是程序化作品，不是精雕成品。滴水兽嘴部有开口薄壁，但没有完整背槽或经过验证的排水通道。外围围墙、角塔布局未调整。历史图中夜景、局部高光等艺术问题仍须由新渲染复核。

动画第 721 帧是与第 1 帧对应的循环端点，只渲染第 1–720 帧；海面采用两层相位错开的互补权重，降低重置接缝，不代表海岸水体物理仿真已通过验证。

工程由项目所有者提供。只发布城堡相关工程、脚本和参考图，不包含私人交接记录、凭据或其他项目。程序化模型和材质未另行授予开源许可证。`MANIFEST.sha256` 记录本轮发布文件摘要。

## 未验收候选

[夜之女王独立候选](candidates/night-queen/README.md)及参考照片已归档供审查。人物造型未获认可，不属于正式场景；不替换滴水兽。
