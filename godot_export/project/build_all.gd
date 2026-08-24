extends SceneTree
# Reads build_manifest.json (written by tools/package_godot.py) and builds one
# SpriteFrames resource per asset: 8 AtlasTexture frames, one per direction,
# indexed so game code can set `.frame = direction_index` directly rather than
# playing an animation -- there is no motion here, just 8 fixed poses of a
# camera-fixed isometric rig. World-space facts (height, footprint, anchor,
# walkable) and per-direction facts (pivot, bbox, azimuth) that don't have a
# native SpriteFrames slot are carried as resource metadata so downstream
# GDScript can read them back with `get_meta()`.
#
# Must run AFTER a `--headless --import` pass on this project (the PNGs under
# assets/ have to already be real, file-backed Texture2D resources -- see
# ART_CRITIQUE.md / NEXT.md "Godot export" notes for why: an un-imported PNG
# loaded via Image.load()+ImageTexture.create_from_image() serializes as a
# bloated inline pixel blob instead of a lightweight ext_resource path).

func _init():
	var f := FileAccess.open("res://build_manifest.json", FileAccess.READ)
	if f == null:
		printerr("build_manifest.json not found -- run tools/package_godot.py first")
		quit(1)
		return
	var data = JSON.parse_string(f.get_as_text())
	f.close()
	if data == null:
		printerr("build_manifest.json: invalid JSON")
		quit(1)
		return

	var out_dir := "res://resources"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out_dir))

	var ok := 0
	var failed := []
	for asset_name in data["assets"].keys():
		var entry = data["assets"][asset_name]
		var frames := SpriteFrames.new()
		frames.remove_animation("default")
		frames.add_animation("idle")
		frames.set_animation_loop("idle", false)
		frames.set_animation_speed("idle", 0.0)

		var pivots := []
		var bboxes := []
		var azimuths := []
		var frame_list = entry["frames"]
		frame_list.sort_custom(func(a, b): return a["direction"] < b["direction"])
		for fr in frame_list:
			var path := "res://assets/%s/%s" % [asset_name, fr["file"]]
			var tex: Texture2D = load(path)
			if tex == null:
				printerr(asset_name, ": failed to load ", path, " (import missing?)")
				failed.append(asset_name)
				continue
			var atlas := AtlasTexture.new()
			atlas.atlas = tex
			atlas.region = Rect2(Vector2.ZERO, tex.get_size())
			frames.add_frame("idle", atlas)
			pivots.append(fr["pivot"])
			bboxes.append(fr["bbox"])
			azimuths.append(fr["azimuth"])

		var world = entry["world"]
		frames.set_meta("height", world["height"])
		frames.set_meta("footprint_xy", world["footprint_xy"])
		frames.set_meta("anchor", world["anchor"])
		frames.set_meta("walkable", world["walkable"])
		frames.set_meta("pivots", pivots)
		frames.set_meta("bboxes", bboxes)
		frames.set_meta("azimuths", azimuths)

		var out_path := "%s/%s.tres" % [out_dir, asset_name]
		var serr = ResourceSaver.save(frames, out_path)
		if serr != OK:
			printerr(asset_name, ": save failed, err ", serr)
			failed.append(asset_name)
			continue
		ok += 1

	print("built ", ok, " SpriteFrames resources in ", out_dir)
	if failed.size() > 0:
		printerr("failed: ", failed)
		quit(1)
		return
	quit(0)
