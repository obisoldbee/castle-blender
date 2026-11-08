# Reconstruction v01 — unfinished shape study

This is an actual geometry rebuild, not the approved castle ornament. It does **not** replace the formal castle scene. Original archived candidates and technical-cleanup study remain available.

## Actual changes
- Replaced the original modern head above the neck with a new continuous sculptural head surface, almond eye surfaces and fitted lid boundaries. Kept soft cheek/jaw masses as a user-directed visual interpretation, not an ancient ethnicity claim.
- Replaced crown curves with eight paired broad-root/tapered horn meshes, a supporting cap and contacting small top disc. The disc is retained because the reference description supports one; uncertain three-dimensional details remain interpretation.
- Brought legs inward, rolled palms toward the front, changed vertical rod symbols to transverse palm rods, and adjusted finger spread. Hand anatomy/contact is not yet approved.
- Removed old wing blades and built continuous wing masses with shorter rounded overlapping primary feathers ending higher on the thigh.
- Rebuilt each lower foot as a connected voxel-unioned foot/root/three-toe/claw mesh. Enlarged joint masses and localized transverse creases instead of uniform dense waves.
- Used neutral clay and saved named verification cameras. Both feet are corrected to a minimum z=.3102m over the platform z=.3100m. Reopened-file verification confirms this 0.2mm geometric clearance, not a physical manufacture tolerance.

## Self-review: still NOT accepted
The face is still too generic: nose/alar volumes are shallow, upper eyelids stiff, and the neck is not yet merged into a production topology. Horn layers remain overly regular and the cap exposes too much conical area in oblique view. The feet retain segmented/tubular joint impressions. Palms/fingers and elbow folds still need reference-driven refinement. The new wing silhouette is closer in height but lacks finalized root/covert transitions. This iteration is useful for checking direction, not a finished replacement.

Do not spend effort on material noise or tiny decorative detail before these large shapes pass review. No claim of archaeological exactness, printable manifold whole figure, or final visual acceptance.

## Reproduce
From this directory, run `blender -b --disable-autoexec --python integrate.py`. It opens `../remediation/Night_Queen_Cleanup_Study.blend`, imports the four local modules, saves the independent output and renders four views. CPU Cycles,48 samples,no denoising. `validate.py` reopens the saved file and verifies the scoped checks. `render_manifest.json` ties the views to the saved model hash.

Source photographs and upstream attribution remain in ../SOURCES.md. No private research conversation or restricted museum-image composites are included here.

Final integrated visual check also shows an ankle/lower-leg ledge in oblique view. Foot meshes themselves are connected, but the body-to-foot junction is not yet seamless; do not confuse the per-foot topology check with whole-character integration.
